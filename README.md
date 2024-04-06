# TP0: Docker + Comunicaciones + Concurrencia

## Instrucciones de uso
El repositorio cuenta con un **Makefile** que posee encapsulado diferentes comandos utilizados recurrentemente en el proyecto en forma de targets. Los targets se ejecutan mediante la invocación de:

* **make \<target\>**:
Los target imprescindibles para iniciar y detener el sistema son **docker-compose-up** y **docker-compose-down**, siendo los restantes targets de utilidad para el proceso de _debugging_ y _troubleshooting_.

Los targets disponibles son:
* **docker-compose-up**: Inicializa el ambiente de desarrollo (buildear docker images del servidor y cliente, inicializar la red a utilizar por docker, etc.) y arranca los containers de las aplicaciones que componen el proyecto.
* **docker-compose-down**: Realiza un `docker-compose stop` para detener los containers asociados al compose y luego realiza un `docker-compose down` para destruir todos los recursos asociados al proyecto que fueron inicializados. Se recomienda ejecutar este comando al finalizar cada ejecución para evitar que el disco de la máquina host se llene.
* **docker-compose-logs**: Permite ver los logs actuales del proyecto. Acompañar con `grep` para lograr ver mensajes de una aplicación específica dentro del compose.
* **docker-image**: Buildea las imágenes a ser utilizadas tanto en el servidor como en el cliente. Este target es utilizado por **docker-compose-up**, por lo cual se lo puede utilizar para testear nuevos cambios en las imágenes antes de arrancar el proyecto.
* **build**: Compila la aplicación cliente para ejecución en el _host_ en lugar de en docker. La compilación de esta forma es mucho más rápida pero requiere tener el entorno de Golang instalado en la máquina _host_.


## Parte 1: Introducción a Docker
En esta primera parte del trabajo práctico se plantean una serie de ejercicios que sirven para introducir las herramientas básicas de Docker que se utilizarán a lo largo de la materia. El entendimiento de las mismas será crucial para el desarrollo de los próximos TPs.

### Ejercicio N°1:
Modificar la definición del DockerCompose para agregar un nuevo cliente al proyecto.

### Ejercicio N°1.1:
Definir un script (en el lenguaje deseado) que permita crear una definición de DockerCompose con una cantidad configurable de clientes.

### Resolución:
* Traducción de la lógica del lado del cliente de Go a Python.
* Agregado de un script bash para generar el archivo docker-compose.yml con el número de clientes como argumento.
* El script mencionado se puede ejecutar con el comando ./generate-docker-compose.sh <number_of_clients> y se modificará según la necesidad de los siguientes ejercicios (por ejemplo volumes)

-----------


### Ejercicio N°2:
Modificar el cliente y el servidor para lograr que realizar cambios en el archivo de configuración no requiera un nuevo build de las imágenes de Docker para que los mismos sean efectivos. La configuración a través del archivo correspondiente (`config.ini` y `config.yaml`, dependiendo de la aplicación) debe ser inyectada en el container y persistida afuera de la imagen (hint: `docker volumes`).

### Resolución:

* Añadido un volumen de Docker en el docker-compose para enlazar los archivos en la carpeta 'config', permitiendo su uso interno dentro de los contenedores evitando que sean estáticos.
* Respectivamente los archivos empleados son `client_config.ini` y `server_config.ini`, en el caso de los clientes, comparten el mismo archivo de configuración. 

-----------------

### Ejercicio N°3:
Crear un script que permita verificar el correcto funcionamiento del servidor utilizando el comando `netcat` para interactuar con el mismo. Dado que el servidor es un EchoServer, se debe enviar un mensaje al servidor y esperar recibir el mismo mensaje enviado. Netcat no debe ser instalado en la máquina _host_ y no se puede exponer puertos del servidor para realizar la comunicación (hint: `docker network`).

### Resolución:
* Añadido un script bash para probar la conexión entre el servidor y el cliente, utilizando el comando netcat y la red de Docker.
* Para ejecutarlo: `./nc.sh <server> <port> <message>`

---------------
### Ejercicio N°4:
Modificar servidor y cliente para que ambos sistemas terminen de forma _graceful_ al recibir la signal SIGTERM. Terminar la aplicación de forma _graceful_ implica que todos los _file descriptors_ (entre los que se encuentran archivos, sockets, threads y procesos) deben cerrarse correctamente antes que el thread de la aplicación principal muera. Loguear mensajes en el cierre de cada recurso (hint: Verificar que hace el flag `-t` utilizado en el comando `docker compose down`).

### Resolución
* Manejo de la señal SIGTERM para un apagado seguro.
* Modificación de la función principal de ejecución (run main function) usando un indicador (flag) keep_running que será modificado al capturar la señal tanto para cliente como para servidor.


-----------------

## Parte 2: Repaso de Comunicaciones

Las secciones de repaso del trabajo práctico plantean un caso de uso denominado **Lotería Nacional**. Para la resolución de las mismas deberá utilizarse como base al código fuente provisto en la primera parte, con las modificaciones agregadas en el ejercicio 4.


### Ejercicio N°5:
Modificar la lógica de negocio tanto de los clientes como del servidor para nuestro nuevo caso de uso.

#### Cliente
Emulará a una _agencia de quiniela_ que participa del proyecto. Existen 5 agencias. Deberán recibir como variables de entorno los campos que representan la apuesta de una persona: nombre, apellido, DNI, nacimiento, numero apostado (en adelante 'número'). Ej.: `NOMBRE=Santiago Lionel`, `APELLIDO=Lorca`, `DOCUMENTO=30904465`, `NACIMIENTO=1999-03-17` y `NUMERO=7574` respectivamente.

Los campos deben enviarse al servidor para dejar registro de la apuesta. Al recibir la confirmación del servidor se debe imprimir por log: `action: apuesta_enviada | result: success | dni: ${DNI} | numero: ${NUMERO}`.

#### Servidor
Emulará a la _central de Lotería Nacional_. Deberá recibir los campos de la cada apuesta desde los clientes y almacenar la información mediante la función `store_bet(...)` para control futuro de ganadores. La función `store_bet(...)` es provista por la cátedra y no podrá ser modificada por el alumno.
Al persistir se debe imprimir por log: `action: apuesta_almacenada | result: success | dni: ${DNI} | numero: ${NUMERO}`.

#### Comunicación:
Se deberá implementar un módulo de comunicación entre el cliente y el servidor donde se maneje el envío y la recepción de los paquetes, el cual se espera que contemple:
* Definición de un protocolo para el envío de los mensajes.
* Serialización de los datos.
* Correcta separación de responsabilidades entre modelo de dominio y capa de comunicación.
* Correcto empleo de sockets, incluyendo manejo de errores y evitando los fenómenos conocidos como [_short read y short write_](https://cs61.seas.harvard.edu/site/2018/FileDescriptors/).

### Resolución:
* Añadida la capa de comunicación entre cliente y servidor.
* La estructura del mensaje: |tamaño|mensaje, donde 'tamaño' facilita la lectura de mensajes y la manipulación de errores.

---------------

### Ejercicio N°6:
Modificar los clientes para que envíen varias apuestas a la vez (modalidad conocida como procesamiento por _chunks_ o _batchs_). La información de cada agencia será simulada por la ingesta de su archivo numerado correspondiente, provisto por la cátedra dentro de `.data/datasets.zip`.
Los _batchs_ permiten que el cliente registre varias apuestas en una misma consulta, acortando tiempos de transmisión y procesamiento. La cantidad de apuestas dentro de cada _batch_ debe ser configurable. Realizar una implementación genérica, pero elegir un valor por defecto de modo tal que los paquetes no excedan los 8kB. El servidor, por otro lado, deberá responder con éxito solamente si todas las apuestas del _batch_ fueron procesadas correctamente.

### Resolución:
* Añadida la característica de leer apuestas por fragmentos (chunks) y enviarlas al servidor.
* Modificación del protocolo de mensaje al formato: |tamaño,flag|mensaje, donde 'tamaño' es la longitud del mensaje y 'flag' es el tipo de mensaje enviado.
* Se agregaron volúmenes de Docker para los datos específicos de la agencia y el almacenamiento de apuestas en el servidor.
* Los flags que se utilizaron fueron 'NORMAL', 'NON_PROTOCOL' y 'BET', siendo este último el enviado cuando el cliente carga apuestas al servidor.
----------------
### Ejercicio N°7:
Modificar los clientes para que notifiquen al servidor al finalizar con el envío de todas las apuestas y así proceder con el sorteo.
Inmediatamente después de la notificacion, los clientes consultarán la lista de ganadores del sorteo correspondientes a su agencia.
Una vez el cliente obtenga los resultados, deberá imprimir por log: `action: consulta_ganadores | result: success | cant_ganadores: ${CANT}`.

El servidor deberá esperar la notificación de las 5 agencias para considerar que se realizó el sorteo e imprimir por log: `action: sorteo | result: success`.
Luego de este evento, podrá verificar cada apuesta con las funciones `load_bets(...)` y `has_won(...)` y retornar los DNI de los ganadores de la agencia en cuestión. Antes del sorteo, no podrá responder consultas por la lista de ganadores.
Las funciones `load_bets(...)` y `has_won(...)` son provistas por la cátedra y no podrán ser modificadas por el alumno.

### Resolución:
* Se implementó la función de sorteo para las agencias en el servidor.
* Como mecanismo para transmitir que todas las apuestas fueron cargadas, se envía un mensaje con flag 'FINAL' y el cuerpo contiene el id de la agencia que lo envía. 
* El servidor espera el mensaje de todas las agencias participantes antes de continuar.
* Se hace el envío de los resultados del sorteo a cada agencia a través de sus respectivos sockets, comunicando únicamente los ganadores de la agencia correspondiente.

------------


## Parte 3: Repaso de Concurrencia

### Ejercicio N°8:
Modificar el servidor para que permita aceptar conexiones y procesar mensajes en paralelo.
En este ejercicio es importante considerar los mecanismos de sincronización a utilizar para el correcto funcionamiento de la persistencia.

En caso de que el alumno implemente el servidor Python utilizando _multithreading_,  deberán tenerse en cuenta las [limitaciones propias del lenguaje](https://wiki.python.org/moin/GlobalInterpreterLock).

### Resolución:
* Procesamiento de conexiones en paralelo en el servidor mediante el módulo multiprocessing.
* Implementación de un sistema de bloqueo para garantizar un acceso seguro y sincronizado a los recursos compartidos, especialmente al archivo bets.csv dado que puede accederse al cargar las apuestas en cada conexión paralela.
----------
### Extra:
* Se agregó el manejo de un timeout para la terminación temprana / inesperada del cliente.
* El servidor envía un mensaje de error a los clientes restantes en caso de que alguno no responda luego de un periodo configurable(en el archivo del volume del servidor) de tiempo, permitiendo su cierre adecuado y la terminación del servidor.
* También se enviará un mensaje con flag error en el caso del sigterm por parte del servidor, esto permite que los clientes puedan desconectarse y no seguir intentando comunicarse con un servidor que pronto finalizará su ejecución.
* Esto permite mejorar la robustez de la comunicación cliente-servidor, garantizando una mejor finalización de procesos bajo condiciones inesperadas.

----------
### Logs:
Caso de ejecución correcta:
* Servidor:
```
2024-03-25 20:40:11 2024-03-25 23:40:11 DEBUG    action: config | result: success | port: 12345 | listen_backlog: 5 | logging_level: DEBUG | time_limit: 10
2024-03-25 20:40:11 2024-03-25 23:40:11 INFO     action: accept_connections | result: in_progress
2024-03-25 20:40:14 2024-03-25 23:40:14 INFO     action: accept_connections | result: success | ip: 172.25.125.3
2024-03-25 20:40:14 2024-03-25 23:40:14 INFO     action: accept_connections | result: in_progress
2024-03-25 20:40:14 2024-03-25 23:40:14 INFO     action: receive_message | result: success | ip: 172.25.125.3 | bets_received: 200
...
2024-03-25 20:40:14 2024-03-25 23:40:14 INFO     action: receive_message | result: success | ip: 172.25.125.3 | bets_received: 191
2024-03-25 20:40:14 2024-03-25 23:40:14 INFO     action: receive_message | result: success | ip: 172.25.125.3 | agency_waiting_raffle: 5
2024-03-25 20:40:14 2024-03-25 23:40:14 INFO     action: accept_connections | result: success | ip: 172.25.125.4
2024-03-25 20:40:14 2024-03-25 23:40:14 INFO     action: accept_connections | result: in_progress
2024-03-25 20:40:14 2024-03-25 23:40:14 INFO     action: receive_message | result: success | ip: 172.25.125.4 | bets_received: 200
...
2024-03-25 20:40:14 2024-03-25 23:40:14 INFO     action: receive_message | result: success | ip: 172.25.125.4 | bets_received: 118
2024-03-25 20:40:14 2024-03-25 23:40:14 INFO     action: receive_message | result: success | ip: 172.25.125.4 | agency_waiting_raffle: 2
2024-03-25 20:40:16 2024-03-25 23:40:16 INFO     action: accept_connections | result: success | ip: 172.25.125.6
2024-03-25 20:40:16 2024-03-25 23:40:16 INFO     action: accept_connections | result: in_progress
2024-03-25 20:40:16 2024-03-25 23:40:16 INFO     action: receive_message | result: success | ip: 172.25.125.6 | bets_received: 200
...
2024-03-25 20:40:16 2024-03-25 23:40:16 INFO     action: receive_message | result: success | ip: 172.25.125.6 | bets_received: 38
2024-03-25 20:40:16 2024-03-25 23:40:16 INFO     action: receive_message | result: success | ip: 172.25.125.6 | agency_waiting_raffle: 4
2024-03-25 20:40:16 2024-03-25 23:40:16 INFO     action: accept_connections | result: success | ip: 172.25.125.5
2024-03-25 20:40:16 2024-03-25 23:40:16 INFO     action: accept_connections | result: in_progress
....
2024-03-25 20:40:17 2024-03-25 23:40:17 INFO     action: accept_connections | result: success | ip: 172.25.125.7
2024-03-25 20:40:17 2024-03-25 23:40:17 INFO     action: receive_message | result: success | ip: 172.25.125.7 | bets_received: 200
...
2024-03-25 20:40:17 2024-03-25 23:40:17 INFO     action: receive_message | result: success | ip: 172.25.125.5 | bets_received: 14
2024-03-25 20:40:17 2024-03-25 23:40:17 INFO     action: receive_message | result: success | ip: 172.25.125.7 | bets_received: 200
2024-03-25 20:40:17 2024-03-25 23:40:17 INFO     action: receive_message | result: success | ip: 172.25.125.5 | agency_waiting_raffle: 3
2024-03-25 20:40:17 2024-03-25 23:40:17 INFO     action: receive_message | result: success | ip: 172.25.125.7 | bets_received: 200
...
2024-03-25 20:40:17 2024-03-25 23:40:17 INFO     action: receive_message | result: success | ip: 172.25.125.7 | bets_received: 136
2024-03-25 20:40:17 2024-03-25 23:40:17 INFO     action: receive_message | result: success | ip: 172.25.125.7 | agency_waiting_raffle: 1
2024-03-25 20:40:18 2024-03-25 23:40:18 INFO     action: raffle | result: success | agency: 5 | winners: 0
2024-03-25 20:40:18 2024-03-25 23:40:18 INFO     action: raffle | result: success | agency: 2 | winners: 6
2024-03-25 20:40:18 2024-03-25 23:40:18 INFO     action: raffle | result: success | agency: 4 | winners: 2
2024-03-25 20:40:18 2024-03-25 23:40:18 INFO     action: raffle | result: success | agency: 3 | winners: 6
2024-03-25 20:40:18 2024-03-25 23:40:18 INFO     action: raffle | result: success | agency: 1 | winners: 5
```
* Cliente 5 no tiene ganadores:
```
2024-03-25 20:40:14 2024-03-25 23:40:14 - INFO - action: config | result: success | client_id: 5 | server_address: server:12345 | loop_lapse: 20.0 | loop_period: 5.0 | log_level: DEBUG
2024-03-25 20:40:14 2024-03-25 23:40:14 - INFO - action: send_bets | result: success | client_id: 5 | bets_sent: 200 | size: 8944
2024-03-25 20:40:14 2024-03-25 23:40:14 - INFO - action: receive_message | result: success | client_id: 5 | server_bets_received: 200
...
2024-03-25 20:40:14 2024-03-25 23:40:14 - INFO - action: receive_message | result: success | client_id: 5 | server_bets_received: 191
2024-03-25 20:40:18 2024-03-25 23:40:18 - INFO - action: client_closed | client_id: 5
```

* CLiente 4 sí tiene ganadores:
```
2024-03-25 20:40:16 2024-03-25 23:40:16 - INFO - action: config | result: success | client_id: 4 | server_address: server:12345 | loop_lapse: 20.0 | loop_period: 5.0 | log_level: DEBUG
2024-03-25 20:40:16 2024-03-25 23:40:16 - INFO - action: send_bets | result: success | client_id: 4 | bets_sent: 200 | size: 8965
2024-03-25 20:40:16 2024-03-25 23:40:16 - INFO - action: receive_message | result: success | client_id: 4 | server_bets_received: 200
...
2024-03-25 20:40:16 2024-03-25 23:40:16 - INFO - action: send_bets | result: success | client_id: 4 | bets_sent: 38 | size: 1776
2024-03-25 20:40:16 2024-03-25 23:40:16 - INFO - action: receive_message | result: success | client_id: 4 | server_bets_received: 38
2024-03-25 20:40:18 2024-03-25 23:40:18 - INFO - action: receive_message | result: success | client_id: 4 | winners_amount: 2
2024-03-25 20:40:18 2024-03-25 23:40:18 - INFO - action: client_closed | client_id: 4
```
------

Caso de shutdown de servidor:
* Servidor informa su shutdown:
```
...
2024-03-25 21:08:27 2024-03-26 00:08:27 INFO     action: receive_message | result: success | ip: 172.25.125.5 | bets_received: 1
2024-03-25 21:08:27 2024-03-26 00:08:27 INFO     action: sigterm_received | result: initiating_shutdown
2024-03-25 21:08:27 2024-03-26 00:08:27 INFO     action: send_error | result: success | ip: 172.25.125.3
2024-03-25 21:08:27 2024-03-26 00:08:27 INFO     action: send_error | result: success | ip: 172.25.125.4
2024-03-25 21:08:27 2024-03-26 00:08:27 INFO     action: send_error | result: success | ip: 172.25.125.5
2024-03-25 21:08:27 2024-03-26 00:08:27 INFO     action: send_error | result: success | ip: 172.25.125.6
2024-03-25 21:08:27 2024-03-26 00:08:27 INFO     action: send_error | result: success | ip: 172.25.125.7
```

* Cliente 1:
```
...
2024-03-25 21:08:27 2024-03-26 00:08:27 - INFO - action: receive_message | result: success | client_id: 4 | server_bets_received: 1
2024-03-25 21:08:27 2024-03-26 00:08:27 - INFO - action: send_bets | result: success | client_id: 4 | bets_sent: 1 | size: 39
2024-03-25 21:08:27 2024-03-26 00:08:27 - INFO - action: receive_message | result: success | client_id: 4 | server_bets_received: Server shutdown
2024-03-25 21:08:27 2024-03-26 00:08:27 - ERROR - action: receive_message | result: connection_timeout | client_id: 4 | error: Server shutdown
2024-03-25 21:08:27 2024-03-26 00:08:27 - INFO - action: client_closed | client_id: 4
```
