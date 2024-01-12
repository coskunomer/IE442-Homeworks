import sqlite3
import streamlit as st
import pandas as pd

def create_tables(cursor, i):
    # Create Periods Table
    cursor.execute('''
    CREATE TABLE periods (
        periodID INTEGER PRIMARY KEY,
        date TEXT
    )
    ''')

    # Create Parts Table
    cursor.execute('''
    CREATE TABLE parts (
        partID INTEGER PRIMARY KEY,
        part_name TEXT,
        lead_time INTEGER,
        inventory INTEGER,
        lot_size INTEGER,
        BOM_level INTEGER
    )
    ''')


    # Create BOM Table
    cursor.execute('''
    CREATE TABLE bom (
        partID INTEGER,
        component_partID INTEGER,
        multiplier INTEGER,
        PRIMARY KEY (partID, component_partID),
        FOREIGN KEY (partID) REFERENCES part(partID),
        FOREIGN KEY (component_partID) REFERENCES part(partID)
    )
    ''')

    # Create MRP Table
    cursor.execute('''
    CREATE TABLE mrp (
        partID INTEGER,
        periodID INTEGER,
        gross_requirements INTEGER,
        scheduled_receipts INTEGER,
        projected_on_hand INTEGER,
        net_requirements INTEGER,
        planned_order_receipt INTEGER,
        planned_order_release INTEGER,
        PRIMARY KEY (partID, periodID),
        FOREIGN KEY (partID) REFERENCES parts(partID),
        FOREIGN KEY (periodID) REFERENCES periods(periodID)
    )
    ''')

    # Create Demand Forecast Table
    cursor.execute('''
    CREATE TABLE demands (
        partID INTEGER,
        periodID INTEGER,
        demand INTEGER,
        cumulative_demand,
        PRIMARY KEY (partID, periodID)
    )
    ''')

    for periodId in range(1, i+1):
        cursor.execute(f'INSERT INTO periods VALUES ({periodId}, "Week {periodId}")')


    # Insert sample data into Parts Table
    cursor.execute('INSERT INTO parts VALUES (1, "Chair", 2, 260, 1, 0)')
    cursor.execute('INSERT INTO parts VALUES (2, "Seat", 2, 60, 1, 1)')
    cursor.execute('INSERT INTO parts VALUES (3, "Back", 2, 40, 1, 1)')
    cursor.execute('INSERT INTO parts VALUES (4, "Legs", 1, 80, 4, 1)')
    cursor.execute('INSERT INTO parts VALUES (5, "Main frame", 1, 40, 1, 2)')
    cursor.execute('INSERT INTO parts VALUES (6, "Frame Support", 1, 160, 4, 2)')

    # Insert sample data into BOM Table
    cursor.execute('INSERT INTO bom VALUES (1, 2, 1)')
    cursor.execute('INSERT INTO bom VALUES (1, 3, 1)')
    cursor.execute('INSERT INTO bom VALUES (1, 4, 4)')
    cursor.execute('INSERT INTO bom VALUES (3, 5, 1)')
    cursor.execute('INSERT INTO bom VALUES (3, 6, 4)')

    # populate INITIAL mrp table for chairs, seats, back, and legs
    for itemId in range(1, 7):
        for periodId in range(1, i+1):
            if itemId == 2 and periodId == 1:
                cursor.execute('INSERT INTO mrp VALUES (2, 1, 0, 50, 0, 0, 0, 0)')
            elif itemId == 3 and periodId == 1:
                cursor.execute('INSERT INTO mrp VALUES (3, 1, 0, 10, 0, 0, 0, 0)')
            else:
                cursor.execute(f'INSERT INTO mrp VALUES ({itemId}, {periodId}, 0, 0, 0, 0, 0, 0)')

def insert_demand_forecast(cursor, demands):
    # Insert demands into the table
    cursor.executemany('INSERT INTO demands VALUES (?, ?, ?, NULL)', demands)

    # Update the cumulative_demand column using a correlated subquery
    cursor.execute('''
    UPDATE demands
    SET cumulative_demand = (
        SELECT SUM(demand)
        FROM demands AS d2
        WHERE d2.partID = demands.partID AND d2.periodID <= demands.periodID
    )
    ''')

def get_required(cursor, parentID):
    # Select children required for the specified parentID from the bom table
    cursor.execute('''
        SELECT component_partID, multiplier
        FROM bom
        WHERE partID = ?
    ''', (parentID,))

    # Fetch all the results
    required_items = cursor.fetchall()

    # Return the results
    return required_items

def update_gross_requirements(cursor):
    # Update gross requirements for all unique partIDs in the demands table
    # Update the mrp table with gross_requirements
    cursor.execute('''
        UPDATE mrp
        SET gross_requirements = d.demand
        FROM demands d
        WHERE mrp.partID = d.partID AND mrp.periodID = d.periodID;
    ''')

    # update initial projected at hand
    cursor.execute('''
        UPDATE mrp
        SET projected_on_hand = (
            SELECT SUM(scheduled_receipts) + (SELECT inventory FROM parts WHERE mrp.partID = parts.partID)
            FROM mrp AS mrp_prev
            WHERE mrp_prev.partID = mrp.partID AND mrp_prev.periodID <= mrp.periodID
        )
    ''')

    # Update the mrp table with projected_on_hand and net_requirements
    cursor.execute('''
        UPDATE mrp
        SET
            projected_on_hand = CASE
                WHEN projected_on_hand - COALESCE((SELECT cumulative_demand FROM demands WHERE demands.partID = mrp.partID AND demands.periodID = mrp.periodID), 0) >= 0
                THEN projected_on_hand - COALESCE((SELECT cumulative_demand FROM demands WHERE demands.partID = mrp.partID AND demands.periodID = mrp.periodID), 0)
                ELSE 0
            END
        WHERE EXISTS (SELECT 1 FROM demands WHERE demands.partID = mrp.partID AND demands.periodID = mrp.periodID)
    ''')

    # Update the mrp table with projected_on_hand and net_requirements
    cursor.execute('''
        UPDATE mrp
        SET
            net_requirements = CASE
                WHEN projected_on_hand = 0 AND gross_requirements > 0
                THEN COALESCE((SELECT demand FROM demands WHERE demands.partID = mrp.partID AND demands.periodID = mrp.periodID), 0) - 
                     CASE
                         WHEN mrp.periodID > 1
                         THEN COALESCE((SELECT projected_on_hand FROM mrp AS mrp2 WHERE mrp2.partID = mrp.partID AND mrp2.periodID = mrp.periodID - 1), 0)
                         ELSE 0
                     END
                ELSE 0
            END
        WHERE EXISTS (SELECT 1 FROM demands WHERE demands.partID = mrp.partID AND demands.periodID = mrp.periodID);
    ''')

    cursor.execute('''
            UPDATE mrp
            SET
                net_requirements = CASE
                    WHEN net_requirements > 0
                    THEN ROUND(net_requirements / (SELECT lot_size FROM parts WHERE parts.partID = mrp.partID)) * (SELECT lot_size FROM parts WHERE parts.partID = mrp.partID)
                    ELSE 0
                END
            WHERE EXISTS (SELECT 1 FROM demands WHERE demands.partID = mrp.partID AND demands.periodID = mrp.periodID);
        ''')

    cursor.execute('''
        UPDATE mrp
        SET
            planned_order_receipt = net_requirements
        WHERE EXISTS (SELECT 1 FROM demands WHERE demands.partID = mrp.partID AND demands.periodID = mrp.periodID);
    ''')

    # Update planner_order_release based on lead time
    cursor.execute('''
            UPDATE mrp
            SET planned_order_release = (
                SELECT net_requirements
                FROM mrp AS mrp_prev
                WHERE mrp_prev.partID = mrp.partID AND mrp_prev.periodID = mrp.periodID + (SELECT lead_time FROM parts WHERE partID = mrp.partID)
            )
            WHERE EXISTS (
                SELECT 1
                FROM demands
                WHERE demands.partID = mrp.partID
                  AND demands.periodID = mrp.periodID
                  AND (mrp.periodID + (SELECT lead_time FROM parts WHERE partID = mrp.partID)) <= (SELECT MAX(periodID) FROM mrp)
            );
        ''')
    update_children(cursor, 1)

def update_children(cursor, parentID):
    children = get_required(cursor, parentID)

    for partID, multiplier in children:
        cursor.execute('''
                    UPDATE mrp
                    SET gross_requirements = COALESCE((
                        SELECT parent_mrp.planned_order_release * ?
                        FROM mrp AS parent_mrp
                        WHERE parent_mrp.partID = ? AND parent_mrp.periodID = mrp.periodID
                    ), 0)
                    WHERE partID = ?;
                ''', (multiplier, parentID, partID))

        # update initial projected at hand
        cursor.execute('''
                UPDATE mrp
                SET projected_on_hand = (
                    SELECT SUM(scheduled_receipts) + (SELECT inventory FROM parts WHERE mrp.partID = parts.partID)
                    FROM mrp AS mrp_prev
                    WHERE mrp_prev.partID = mrp.partID AND mrp_prev.periodID <= mrp.periodID
                )
                WHERE mrp.partID = ?
            ''', (partID,))
        # update projected at hand
        cursor.execute('''
                    UPDATE mrp
                    SET projected_on_hand = CASE
                        WHEN COALESCE(mrp.projected_on_hand, 0) - (
                            SELECT SUM(COALESCE(parent_mrp.gross_requirements, 0))
                            FROM mrp AS parent_mrp
                            WHERE parent_mrp.partID = ? AND parent_mrp.periodID <= mrp.periodID
                        ) > 0
                        THEN COALESCE(mrp.projected_on_hand, 0) - (
                            SELECT SUM(COALESCE(parent_mrp.gross_requirements, 0))
                            FROM mrp AS parent_mrp
                            WHERE parent_mrp.partID = ? AND parent_mrp.periodID <= mrp.periodID
                        )
                        ELSE 0
                    END
                    WHERE partID = ?;
                ''', (partID, partID, partID))

        # Update net_requirements for each child based on the demand and previous projected_on_hand
        cursor.execute('''
                    UPDATE mrp
                    SET 
                        net_requirements = CASE
                            WHEN COALESCE(mrp.projected_on_hand, 0) = 0 AND COALESCE(mrp.gross_requirements, 0) > 0
                            THEN ABS(gross_requirements - 
                                CASE
                                    WHEN mrp.periodID > 1
                                    THEN COALESCE((SELECT projected_on_hand FROM mrp AS mrp2 WHERE mrp2.partID = mrp.partID AND mrp2.periodID = mrp.periodID - 1), 0)
                                    ELSE 0
                                END)
                            ELSE 0
                        END,
                        planned_order_receipt = CASE
                            WHEN COALESCE(mrp.projected_on_hand, 0) = 0 AND COALESCE(mrp.gross_requirements, 0) > 0
                            THEN ABS(gross_requirements - 
                                CASE
                                    WHEN mrp.periodID > 1
                                    THEN COALESCE((SELECT projected_on_hand FROM mrp AS mrp2 WHERE mrp2.partID = mrp.partID AND mrp2.periodID = mrp.periodID - 1), 0)
                                    ELSE 0
                                END)
                            ELSE 0
                    END
                    WHERE partID = ?;
                ''', (partID,))
        # Update planner_order_release based on lead time
        cursor.execute('''
            UPDATE mrp
            SET planned_order_release = (
                SELECT ROUND(COALESCE(net_requirements, 0) / parts.lot_size) * parts.lot_size
                FROM mrp AS mrp_prev
                JOIN parts ON mrp_prev.partID = parts.partID
                WHERE mrp_prev.partID = mrp.partID AND mrp_prev.periodID = mrp.periodID + (SELECT lead_time FROM parts WHERE partID = mrp.partID)
            )
            WHERE EXISTS (
                SELECT 1
                FROM mrp
                WHERE mrp.partID = ?
                    AND (mrp.periodID + (SELECT lead_time FROM parts WHERE partID = mrp.partID)) <= (SELECT MAX(periodID) FROM mrp)
            );
        ''', (partID,))

        if len(get_required(cursor, partID)) > 0:
            update_children(cursor, partID)

    cursor.execute('''
                UPDATE mrp
                SET planned_order_release = COALESCE(planned_order_release, 0)
                WHERE planned_order_release IS NULL;
            ''')

def main():
    # Set layout to wide and display centered content
    st.set_page_config(layout="wide")
    # Create a mapping of part IDs to names
    part_mapping = {
        1: "Chair",
        2: "Seat",
        3: "Back",
        4: "Legs",
        5: "Main frame",
        6: "Frame Support"
    }
    # Set page configuration for full width
    st.title("MRP Calculator")

    st.header("Ömer Coşkun - 2019402177")

    # Input form for required data
    st.header("Input Data")

    # Dynamic demand forecast input
    st.header("Demand Forecast")
    num_periods = st.number_input("Number of Periods", min_value=8, value=8)

    # Use st.columns for horizontal layout
    max_columns = 8
    num_rows = -(-num_periods // max_columns)
    columns = st.columns(max_columns)

    demands = []
    initial_demand_values = [150, 0, 70, 0, 175, 0, 90, 60]

    for row in range(num_rows):
        for col in range(max_columns):
            i = row * max_columns + col + 1
            if i > num_periods:
                break
            if i > 8:
                period_demand = columns[col].number_input(f"Week {i} Demand", min_value=0,
                                                          value=0)
            else:
                period_demand = columns[col].number_input(f"Week {i} Demand", min_value=0,
                                                      value=initial_demand_values[i - 1])
            demands.append(period_demand)

    if st.button("Run MRP Calculation"):
        # Connect to SQLite database
        conn = sqlite3.connect('mrp_db.db')
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS demands")
        cursor.execute("DROP TABLE IF EXISTS periods")
        cursor.execute("DROP TABLE IF EXISTS parts")
        cursor.execute("DROP TABLE IF EXISTS mrp")
        cursor.execute("DROP TABLE IF EXISTS bom")

        # Create tables if not exists
        create_tables(cursor, num_periods)

        # Prepare demands list for insertion
        demands_list = [(1, i, demand) for i, demand in enumerate(demands, start=1)]

        # Insert demand forecast into demands table
        insert_demand_forecast(cursor, demands_list)

        # Update gross requirements based on the demand forecast
        update_gross_requirements(cursor)

        # Commit the changes and close the connection
        conn.commit()

        # Fetch and display MRP tables for each unique part ID
        cursor.execute("SELECT DISTINCT partID FROM mrp")
        unique_part_ids = [row[0] for row in cursor.fetchall()]
        for part_id in unique_part_ids:
            part_name = part_mapping.get(part_id, f"Unknown Part ({part_id})")
            st.subheader(f"MRP Table for Part: {part_name}")

            cursor.execute(f"SELECT * FROM mrp WHERE partID = {part_id}")
            mrp_table = cursor.fetchall()

            # Convert the MRP table to a DataFrame for better styling
            columns = [
                "partID",
                "Period ID",
                "Gross Requirements",
                "Scheduled Receipts",
                "Projected On Hand",
                "Net Requirements",
                "Planned Order Receipt",
                "Planned Order Release"
            ]
            mrp_df = pd.DataFrame(mrp_table, columns=columns)

            # Display the DataFrame with enhanced styling
            st.dataframe(mrp_df.style.set_table_styles([{
                'selector': 'thead',
                'props': [
                    ('background-color', '#3F88C5'),
                    ('color', 'white'),
                    ('font-weight', 'bold')
                ]
            }, {
                'selector': 'tbody',
                'props': [
                    ('font-size', '12px')
                ]
            }]))

        # Close the connection
        conn.close()

        st.success("MRP Calculation completed successfully!")
        conn.close()

if __name__ == "__main__":
    main()