# tcup



Assumption: JSON data is pushed to Kafka topic
Setup environment-> We are using Docker Desktop
Download HiveMQ and place it in a directory
c:/<name of directory>docker run -p 8080:8080 -p 1883:1883 hivemq/hivemq4
Open a browser window
http://localhost:8080
You can login with the default credentials:
User: admin
Password: hivemq
Reference: https://www.hivemq.com/downloads/docker/

Place the docker-compose.yml file in a directory
c:/<name of directory>
Open a command prompt and make sure docker is running
c:/<name of directory>docker-compose up -d

c:/<name of directory>docker-compose ps

Create Kafka Topic->
c:/<name of directory>docker exec broker kafka-topics --if-not-exists --zookeeper zookeeper:2181 --create --partitions 1 --replication-factor 1 --topic device_data
OR
c:/<name of directory>docker-compose exec broker kafka-topics --create --topic device_data --partitions 3 --replication-factor 1 --if-not-exists --bootstrap-server broker:9092
Connect ksqlDB->
c:/<name of directory>docker exec -it ksqldb ksql http://ksqldb:8088
Create ksqlDB objects->
ksql>show topics;
ksql>create stream stream_device_data  (who varchar, batt INTEGER, lon DOUBLE, lat DOUBLE, timeepoc BIGINT, alt INTEGER, speed DOUBLE) 
with (kafka_topic = 'device_data', value_format='JSON');

ksql>SET 'auto.offset.reset'='earliest';

ksql>CREATE table table_runner_status with (value_format='JSON') AS 
select who
, min(speed) as min_speed
, max(speed) as max_speed
, min(GEO_DISTANCE(lat, lon, 22.501193, 88.410533, 'km')) as dist_to_finish
, count(*) as num_events 
from stream_device_data WINDOW TUMBLING (size 1 minute) 
group by who;

ksql>create stream stream_runner_location with (value_format='JSON') as
select who
, timeepoc as event_time
, cast(lat as varchar) +','+cast(lon as varchar) as LOCATION
, alt
, batt
, speed
from stream_device_data ;

Query objects to verify data is coming once the MQTT publisher/subscriber program is run->

ksql>select * from stream_device_data emit changes limit 10;

ksql>select * from table_runner_status emit changes limit 10;

ksql>select * from stream_runner_location emit changes limit 10;

Create Elasticsearch Sink connector->
ksql>CREATE SINK CONNECTOR SINK_ELASTIC_DEVICE_DATA WITH (
 'connector.class'= 'io.confluent.connect.elasticsearch.ElasticsearchSinkConnector',
 'connection.url'= 'http://elasticsearch:9200',
 'tasks.max'= '1',
 'topics'= 'stream_device_data',
 'name'= 'SINK_ELASTIC_DEVICE_DATA',
 'type.name'= '_doc',
 'value.converter'= 'org.apache.kafka.connect.json.JsonConverter',
 'value.converter.schemas.enable'= 'false',
 'schema.ignore'= 'true',
 'key.ignore'= 'true'
);

ksql>CREATE SINK CONNECTOR SINK_ELASTIC_RUNNER_STATUS WITH (
 'connector.class'= 'io.confluent.connect.elasticsearch.ElasticsearchSinkConnector',
 'connection.url'= 'http://elasticsearch:9200',
 'tasks.max'= '1',
 'topics'= 'table_runner_status',
 'name'= 'SINK_ELASTIC_RUNNER_STATUS',
 'type.name'= '_doc',
 'value.converter'= 'org.apache.kafka.connect.json.JsonConverter',
 'value.converter.schemas.enable'= 'false',
 'schema.ignore'= 'true',
 'key.ignore'= 'true'
);

ksql>CREATE SINK CONNECTOR SINK_ELASTIC_RUNNER_LOCATION WITH (
 'connector.class'= 'io.confluent.connect.elasticsearch.ElasticsearchSinkConnector',
 'connection.url'= 'http://elasticsearch:9200',
 'tasks.max'= '1',
 'topics'= 'stream_runner_location',
 'name'= 'SINK_ELASTIC_RUNNER_LOCATION',
 'type.name'= '_doc',
 'value.converter'= 'org.apache.kafka.connect.json.JsonConverter',
 'value.converter.schemas.enable'= 'false',
 'schema.ignore'= 'true',
 'key.ignore'= 'true'
);


Sample Steps To Run Windows executable files:
----------------------------------------------
A. HiveKafkaConnector:

1. Change the parameter values as per expectation in properties file (HiveMQ.properties) mentioned in point 3 (--propertiesfile value)
2. Open command-prompt in Windows
3. execute command: cd C:\Projjwal\Python_Projects\Executable_Files\HiveKafkaConnector\Connector1
4. execute command: HiveKafkaConnector --propertiesfile C:/Projjwal/Python_Projects/Executable_Files/HiveKafkaConnector/Connector1/HiveMQ.properties

B. HiveProducer1:

1. Change the parameter values as per expectation in properties file (Producer.properties) mentioned in point 3 (--propertiesfile value)
2. Open command-prompt in Windows
3. execute command: cd C:\Projjwal\Python_Projects\Executable_Files\HiveProducer\Producer1
4. execute command: HiveMQProducer --inputfile C:/Projjwal/Python_Projects/Executable_Files/HiveProducer/Producer1/Test_Data.txt --propertiesfile C:/Projjwal/Python_Projects/Executable_Files/HiveProducer/Producer1/Producer.properties

C. HiveProducer2(If need to simulate simultaneously two devices):

1. Change the parameter values as per expectation in properties file (Producer.properties) mentioned in point 3 (--propertiesfile value)
2. Open command-prompt in Windows
3. execute command: cd C:\Projjwal\Python_Projects\Executable_Files\HiveProducer\Producer1
4. execute command: HiveMQProducer --inputfile C:/Projjwal/Python_Projects/Executable_Files/HiveProducer/Producer2/Test_Data.txt --propertiesfile C:/Projjwal/Python_Projects/Executable_Files/HiveProducer/Producer1/Producer.properties

D. KafkaConsumer(If Required):

1. Open command-prompt in Windows
2. execute command: cd C:\Projjwal\Python_Projects\Executable_Files\KafkaConsumer\Consumer1
3. execute command: KafkaConsumer --kafkagroup python-consumer --kafkahost localhost --kafkaport 9092 --kafkatopics first_topic --kafkasessionout 30000

Please Note : Sequence to start execution- 1.HiveKafkaConnector 2.KafkaConsumer(Optional) 3.HiveProducer1 4.HiveProducer2(Optional)


High Level Flow Regarding Shared Codes Of Different Components:
----------------------------------------------------------------
A. PyCharm Project :MQTT_PRODUCER
prerequisite : 
1. Need to install Python 3.11.1
2. Need to install paho-mqtt 1.6.1
3. Need to install protobuff 3.20.0

High-Level-Flow:
1. Program flow starts from main.py(__name__ == '__main__')
2. Takes user arguments for input file to be processed and properties file to be used(parameter names : --inputfile,--propertiesfile)
3. Load Properties File 
4. Initialize global veriables taken input from properties file
5. Create the node death payload
6. Set up the MQTT client connection
7. Setup short delay to allow connect callback to occur
8. Publish the birth certificates(NBIRTH & DBIRTH)
	NBIRTH:
	a. Create the node birth payload
	b. Set up the Node Controls
	c. Publish the node birth certificate
	DBIRTH:
	a. Get the payload
	b. Add some device metrics
	c. Publish the initial data with the Device BIRTH certificate
9. Read line by line from a input file(given as parameter in --inputfile) after some time internal to produce device input
10. Setup a short 2 second delay before reading the next line and creating the message payload for first line and to send the message to HiveMQ
11. While reading one-by-one line from input file, checking if the fields present in input jason also present in properties file or not
12. Once fields matching are done, creates the HiveMQ messge payload based to the input types for each field mentioned in properties file under "FileInputSchema" and the corresponding field value present in input line
13. Serialize the message as per protobuf template(schema mentioned in proto file and corresponding sparkplug_b_pb2 class file)
14. Sends the HiveMQ message to the configured topic(mentioned in properties file)

B. PyCharm Project :HiveMQ
prerequisite : 
1. Need to install Python 3.11.1
2. Need to install paho-mqtt 1.6.1
3. Need to install confluent_kafka 2.0.2

High-Level-Flow:
1. Program flow starts from main.py(__name__ == '__main__')
2. Takes user arguments for properties file to be used(parameter name : --propertiesfile)
3. Load Properties File
4. Initializing Global Variables
5. Start to create connection for each client mentioned in properties file, start one thraed for each client & staty connected
6. Start subscribing the message for each client(call subscribe() method inside Create_connections())
	SUBSCRIBE:
	a. Parse only the DDATA message coming from respective client only
	b. Deserialize the message as per payload structure definition mentioned in sparkplug_b_pb2 file
	c. parse the field data as per field type mentioned in properties file schema field mentioned
	d. create a JSON object as per expected format
	d. create a kafka connection
	e. Publish the JSON to the configured kafka topic(mentioned in properties file)
	
Please Note : If you want to run multiple HiveMqProducer clients, all should be configured in HiveMQ properties first. Similarly, if you change the input schema definition(means add/update/delete any parameter, same thing need to be reflected in HiveMQ properties file as well. 

C. PyCharm Project :KafkaConsumer ( Optional to go through this project, since only used for unit testing purpose & to check intermediate flow)
prerequisite : 
1. Need to install Python 3.11.1
2. Need to install confluent_kafka 2.0.2

High-Level-Flow:
1. Program flow starts from main.py(__name__ == '__main__')
2. Takes user arguments to be used(parameter name : --kafkagroup, --kafkahost, --kafkaport, --kafkatopics, --kafkasessionout)
3. Load Properties
4. Initializing Golbal Veriables
5. Create Consumer instance
6. Start Subscribing to topic
7. Read messages from Kafka topic & print to stdout


Open Kibana in a browser window->
http://localhost:5601/app/home

Now create index patterns 
Go to Discover and carry out data analysis

Reporting CLI->
Open a command prompt having Python 3 installed
Navigate to the directory where python-cli2.py is placed for example:
c:/<path to directory>python python-cli2.py -b http://localhost:8088 -t table_runner_status -o c:/<path to directory>file.json
Once report is created exit by Crtl+C and terminate command prompt
