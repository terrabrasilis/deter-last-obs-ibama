## DETER last observation

***Used on the DETER to IBAMA databases.**

Automation to read the weekly cmask data from the HTTP download page, extract the non-cloud pixel values, calculate the last observed day for each polygon, and write the results to database tables.

The expected periodicity is daily for the acquisition and calculation of new data.

For more details, access the [TerraBrasilis Platform's autonomous tasks](https://github.com/terrabrasilis/docker-stacks/tree/master/terrabrasilis-standalone-tasks).

This container is used into the permanent-tasks.yaml file in the [docker-stack](https://github.com/terrabrasilis/docker-stacks.git) repository.

## Configurations

Preconditions:

 - DETER databases has some specific tables;
 - Configuration files to provide parameters for connecting to databases, one for each biome: (Amazonia and Cerrado);
 - Define the environment variable;
 - Define and provide, per volume, a directory to store GeoTiff files and other stuffs;

### Database configuration file

It needs a configuration file to compose the execution environment, as follows:

 - config/pgconfig_<biome_name> (database settings to read and write data)

Create a data directory to write the output files and the "config" directory inside. In this directory, we place the pgconfig.

#### Config details

 > Content of pgconfig file
```txt
user="postgres"
host="localhost"
port="5432"
database="db_name"
password="postgres"
```

### Environment variables

To control the execution, we can define the environment variables as follows.

 > BASE_URL: Optional parameter to be passed to the container instance. The base URL where the cmask files are located.


The examples for setting these variables inside the docker compose fragment.
```yaml
   ...
   environment:
      # cmask files source
      - "BASE_URL=http://cbers9.dpi.inpe.br:8089/files"
   volumes:
   # one directory as volume to store files
      - '/a/directory/to/store/data:/usr/local/data'
   ...
```

## Deploy

To deploy this container, we provide an example in docker compose format in the [docker-compose.yaml](./docker-compose.yml) file.

To run it, an example command is:

```sh
# to up the stack
docker compose -f docker-compose.yaml up -d

# and to stop
docker compose -f docker-compose.yaml down
```


## About code

Adapted from the original by Luis Eduardo P. Maurano <luis.maurano@inpe.br>