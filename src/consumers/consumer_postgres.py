import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from kafka import KafkaConsumer
from models import ride_deserializer

server = 'localhost:9092'
topic_name = 'green-trips'

# Connect to PostgreSQL
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='postgres',
    user='postgres',
    password='postgres'
)
conn.autocommit = True
cur = conn.cursor()

consumer = KafkaConsumer(
    topic_name,
    bootstrap_servers=[server],
    auto_offset_reset='earliest',
    group_id='green-trips-to-postgres-replay-2',
    value_deserializer=ride_deserializer,
    consumer_timeout_ms=10_000,  # 10 secondes sans message => StopIteration
)

print(f"Listening to {topic_name} and writing to PostgreSQL...")

count = 0
for message in consumer:
    ride = message.value

    pickup_dt = datetime.strptime(ride.lpep_pickup_datetime, '%Y-%m-%d %H:%M:%S')
    dropoff_dt = datetime.strptime(ride.lpep_dropoff_datetime, '%Y-%m-%d %H:%M:%S')

    cur.execute(
        """INSERT INTO processed_events
           (
            pickup_datetime,
            dropoff_datetime,
            PULocationID,
            DOLocationID,
            passenger_count,
            trip_distance,
            tip_amount,
            total_amount
           )
           VALUES (
           %s, 
           %s, 
           %s, 
           %s, 
           %s, 
           %s, 
           %s, 
           %s)""",
        (
            pickup_dt,
            dropoff_dt,
            ride.PULocationID, 
            ride.DOLocationID,
            ride.passenger_count, 
            ride.trip_distance, 
            ride.tip_amount, 
            ride.total_amount 
            )
    )
    # count += 1
    # if count % 100 == 0:
    #     print(f"Inserted {count} rows...")

consumer.close()
cur.close()
conn.close()
