import json
import click
from ksql import KSQLAPI

@click.command()
@click.option('--bootstrap-server', '-b', default='http://localhost:8088', help='Kafka bootstrap server')
@click.option('--topic', '-t', required=True, help='Kafka topic name')
@click.option('--output-file', '-o', required=True, help='Output file name')
def read_kafka_topic_json(bootstrap_server, topic, output_file):
	client = KSQLAPI(bootstrap_server)
	query = client.query('select * from '+topic+' emit changes')
	
	with open(output_file, 'w') as f:
		for item in query:
			print(item)
			f.write(json.dumps(item) + '\n')
			f.flush()

	print(f'Finished writing messages from {topic} to {output_file}')


if __name__ == '__main__':
	read_kafka_topic_json()
