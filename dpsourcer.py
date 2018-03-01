#!/usr/bin/env python
version = "2.0"


#Autor: franciscofregona@gmail.com
#https://github.com/franciscofregona '2018
#Esta obra esta sujeta a la licencia -Reconocimiento-NoComercial 4.0 Internacional- de Creative Commons.
#Para ver una copia de esta licencia, visite http://creativecommons.org/licenses/by-nc/4.0/.


#Para obtenerSubdirectorios
import os, os.path

# nombres del servidor actual para poner en la salida.
servidor = ""
vruta = ""

#Si una ruta supera ese valor, ha de subdividirse.
#valor en "puntos"
umbral = 100

#Cuidado: la salida de debug no va a los archivos de salida, solo a la salida de error estandar.
import logging
#Para score y obtenerArchivos
from subprocess import Popen, PIPE


def pprint(item,archivosalida=''):
	"""
	Imprime un diccionario, con indentaciones para legibilidad.
	"""
	print(json.dumps(item, indent=4))

def calcularTamano(ruta):
	"""
	Obtiene el tamano de un directorio y subdirectorios.
	Invoca un simple <du -bs> de sistema operativo.
	"""
	comando1 = Popen(["du", ruta, "-bs"], stdout=PIPE, stderr=PIPE)
	salida = comando1.communicate()
	if len(salida[1]): #ocurrio error
		logging.error(salida[1])
		return 0
	else:
		return int(salida[0].split()[0])

def calcularNumero(ruta):
	"""
	Obtiene el numero (aprox) de archivos y subdirectorios contenidos en un directorio.
	Invoca un simple <ls -R1 | wc -l> de sistema operativo.
	"""
	comando1 = Popen(["ls", ruta, "-R1"], stdout=PIPE, stderr=PIPE)
	comando2 = Popen(["wc", "-l"], stdin=comando1.stdout, stdout=PIPE, stderr=PIPE)
	salida = comando2.communicate()
	if len(salida[1]): #ocurrio error
		logging.error(salida[1])
		return 0
	else:
		return int(salida[0])


def analizar(ruta, profundidad = 2):
    """rutina de analisis.
    ruta: obviamente la ruta a analizar
    profundidad: profundidad maxima a la que se bajara. Se invoca con -1 para evitar pasarse de mambo.

    Si es invocado con profundidad 0 quiere decir que al que ejecuta no le interesa partir mas abajo.
    Responder con un los valores sin mayor exploracion, obtenidos con un simple du para tamano y mlocate
    para numero.

    Salida:
    {'s' : int,     #Suma en bytes de los archivos contenidos en el directorio.
    'n'  : int,     #numero de archivos contenidos en el directorio.
    'hs' : int,		#suma en bytes de los archivos contenidos en los subdirectorios.
    'hn' : int,		#numero de archivos contenidos en los subdirectorios.
    'h'  : {}       #directorios hijos
    }
    """
    tamano = 0
    numero = 0
    tamSubs = 0
    numSubs = 0
    # h = {}
    subs = []
    # files = []	#Eliminado. No es importante y abulta la salida.
    if profundidad < 1:
        tamano = calcularTamano(ruta)
        numero = calcularNumero(ruta)
        return {'name': ruta, 'tamano': tamano, 'numero': numero, 'subs': subs, 'tamSubs': tamSubs, 'numSubs': numSubs}
    else:
        entries = os.listdir(ruta)
        for e in entries:
            rutacompleta = os.path.join(ruta, e)
            #Los links dan error, asi que los salteamos
            if os.path.islink(rutacompleta):
                continue
            # TODO? Agregar excepciones
            # elif e in excepciones:
            # 	continue
            elif os.path.isfile(rutacompleta):
                tamano = tamano + os.stat(rutacompleta).st_size
                numero = numero + 1
                # files.append(e)  #Eliminado. No es importante y abulta la salida.
            elif os.path.isdir(rutacompleta):
                undic = analizar(rutacompleta, profundidad -1)
                subs.append(undic)
                tamSubs = tamSubs + undic['tamano'] + undic['tamSubs']
                numSubs = numSubs + undic['numero'] + undic['numSubs']
        return {'name': ruta, 'tamano': tamano, 'numero': numero, 'subs': subs,
         'tamSubs': tamSubs, 'numSubs': numSubs}

def iterador(diccionario, pesoUmbral, numeroUmbral):
	"""
	parametros:
	* pesoUmbral, numeroUmbral: umbral que determina si algo es "grande",
	segun su tamano o numero de archivos.
	* diccionario: diccionario con la ruta analizada y masticada (por la
	rutina analizar()). Tiene la forma definida por la siguiente sintaxis:
	
	peso ::= <n> (tamano del directorio y subs en bytes)
	numero ::= <n> (numero de archivos contenidos en el directorio y subs)
	diccionario ::= <{'s': <peso>, 'n': <numero>, 'h(ijos)': [<diccionario>]}>
	(es una definicion recursiva: cada directorio tiene una lista de subdirectorios)
	
	salida: lista de rutas

	"""
	logging.debug('Iniciando Iterador. Rutas={}, PesoUmbral={}, NumeroUmbral={}'.format(diccionario, pesoUmbral, numeroUmbral))
	# iterar = True
	entrada = [diccionario]
	salida = []
	while entrada != []:
		logging.debug("iterador: iniciando con entrada: {}".format(entrada))
		cabezaLista = entrada[0]
		# Si un directorio no tiene subdirectorios, o si tiene archivos
		if (cabezaLista['subs'] == []) or (cabezaLista['numero'] != 0):
			# se agrega a la salida independientemente de su tamano...
			salida.append(cabezaLista['name'])
			# y se quita de la lista de entrada.
			logging.debug("iterador: Directorio agregado por no tener subs o tener files.")
			del entrada[0]
		
		#Directorio pequenio, se agrega sin mas
		elif ((cabezaLista['tamano'] + cabezaLista['tamSubs']) <= pesoUmbral) and (cabezaLista['numSubs'] <= numeroUmbral):
			salida.append(cabezaLista['name'])
			logging.debug("iterador: Directorio pequenio={}".format(cabezaLista['tamano'] + cabezaLista['tamSubs']))
			del entrada[0]
		else:
			# Agregamos los subdirectorios a la lista de entrada
			# Ya determinamos que esta lista no esta vacia en el if anterior.
			entrada = entrada + cabezaLista['subs']
			#y quitamos este elemento de la cabecera de la lista.
			del entrada[0]
			logging.debug("iterador: No se agrega dir. a la salida, se agregan subdirectorios a entrada")
	return salida


if __name__ == "__main__":
	import argparse
	import sys
	import json

	#https://docs.python.org/2.7/library/argparse.html
	parser = argparse.ArgumentParser(
		description="Divisor de ruta segun tamano para sources de DataProtect",
		epilog="Procesamiento distribuido. Frank@5123 nov/17")

	parser.add_argument('servidor',
		type=str, #Default: string
		help='Nombre del servidor o hostname, como figura en Data Protector',
		)
	parser.add_argument('ruta',
		type=str, #default string
		help='Ruta o Path a explorar. Frecuentemente se utiliza "/srv".',
		)
	parser.add_argument('-s',
		type=int,
		required=True,
		help='Peso/tamano maximo (en bytes) utilizado para juzgar la necesidad de subdividir un directorio en multiples sources.',
		dest='peso',
		)
	parser.add_argument('-n',
		type=int,
		required=True,
		help='Numero maximo de archivos utilizado para juzgar la necesidad de subdividir un directorio en multiples sources.',
		dest='numero',
		)
	parser.add_argument('-p',
		type=int,
		required=True,
		help='Profundidad maxima para el analisis detallado (luego hace un simple <du>).\nSe recomienda setear a lo que ya se obtuvo como salida en una ejecucion previa +1',
		dest='profundidad',
		)
	parser.add_argument('-v','--version', #
		action='version',
		version='%(prog)s version ' + version,
		help='Muestra el numero de version y sale.'
		)
	parser.add_argument('-d',#debug, opcional
		type=str,
		choices=["CRITICAL","ERROR","WARNING","INFO","DEBUG","NOTSET"],
		required=False,
		help='(Opcional) Salida de depuracion o debug.',
		dest='debug',
		default='CRITICAL'
		)
	parser.add_argument('archivosalida', #Archivo de salida. Opcional
		nargs='?',
		type=argparse.FileType('w'),
		default=sys.stdout,
		help='(Opcional) Nombre de archivo de salida. De no completarse, se usa la salida estandar.',
		)

	############Capturar parametros
	args =  parser.parse_args()
	
	debugs = {
		"CRITICAL": logging.CRITICAL,
		"ERROR": logging.ERROR,
		"WARNING": logging.WARNING,
		"INFO": logging.INFO,
		"DEBUG": logging.DEBUG,
		"NOTSET": logging.NOTSET,
	}

	logging.basicConfig(level=debugs[args.debug])
	
	logging.info(
"""
---------------------
Parametros recibidos:
Archivo de salida: {}
debug level: {}
Tamano maximo por directorio: {}
Numero maximo por directorio: {}
Profundidad de analisis: {}
Ruta del servidor a analizar: {}
Nombre del servidor: {}

""".format(repr(args.archivosalida).split("'")[1], args.debug, args.peso, args.numero,args.profundidad, args.ruta, args.servidor))

	numeroUmbral = args.numero
	pesoUmbral = args.peso
	# nombres del servidor actual para poner en la salida.
	servidor = args.servidor
	vruta = args.ruta
	profundidad = args.profundidad

	#Composicion del diccionario de salida para json
	dic = {}
	dic["servidor"] = servidor
	dic["arbol"] = analizar(vruta, profundidad)
	logging.info("""
Directorio analizado:
{}: {} bytes en {} archivos (todos los numeros aproximados).
""".format(dic['arbol']['name'], dic['arbol']['tamano'] + dic['arbol']['tamSubs'], dic['arbol']['numero'] + dic['arbol']['numSubs']))
	###########Obtener una lista de resultados
	dic["salida"] = iterador(dic['arbol'], args.peso, args.numero)
	
	
	# ########## Agrupar resultados segun peso
	# agrupados = agruparRecursos(lista,umbral)
	# salida = repr(agrupados)
	# dic["sources"] = agrupados
	
	########## Imprimir la salida
	# archivosalida es el archivo pasado por parametro.
	# Y como defaultea a sys.stdout, si no se paso nada, imprime por consola.
	json.dump(dic['salida'],args.archivosalida)

	logging.debug("""
------------------
Salida completa obtenida
{}
""".format(dic))
#Fin
