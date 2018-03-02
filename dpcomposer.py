#!/usr/bin/env python
version = "2.0"


#Autor: franciscofregona@gmail.com
#https://github.com/franciscofregona '2018
#Esta obra esta sujeta a la licencia -Reconocimiento-NoComercial 4.0 Internacional- de Creative Commons.
#Para ver una copia de esta licencia, visite http://creativecommons.org/licenses/by-nc/4.0/.

#Ejemplo de template (tipo jinja2, archivo.j2)
#{% for group in groups %}
#FILESYSTEM "{{group.description}}" {{group.client}}:"{{group.basepath}}"
#{
#	-trees{% for path in group.trees %}
#		"{{path}}"{% endfor %}
#}
#{% endfor %}

import argparse
import jinja2 
import sys
import json
#Cuidado: la salida de debug no va a los archivos de salida, solo a la salida de error estandar.
import logging

def leerJson(archivo):
	"""
	Toma una parametro string con la ruta del archivo a deserializar
	devuelve un objeto de Python.
	"""
	with open(archivo) as json_file:
		data = json.load(json_file)
	return data

def componerGrupos(objeto):
	"""
	Toma el objeto (diccionario con una lista de paths) leido por el lector de Json
	y se compone (y retorna) una lista de diccionarios de la forma:
	# g1 = {}
	# g1["description"] = "d"
	# g1["client"] = "c"
	# g1["basepath"] = "/tmp"
	# g1["paths"] = ["/tmp/1","/tmp/2","/tmp/otraruta"]
	salida.append(g1)
	"""
	salida = []
	contador = 0
	for s in objeto['salida']:
		g1 = {}
		g1['client'] = objeto['servidor']
		g1['basepath'] = objeto['vruta']
		g1['description'] = g1['basepath'] + "_" + str(contador)
		
		# El json trajo los pesos de cada elemento, no nos interesan.
		trees = []
		# for elemento in s:
		# 	trees.append(elemento[0])
		# g1['trees'] = trees
		g1['trees'] = [s]

		salida.append(g1)
		contador = contador + 1

	return salida


def renderear(groups):
	"""
	Carga el template en el directorio local e instancia en el el diccionario groups parametro.
	"""
	templateLoader = jinja2.FileSystemLoader( searchpath="./")
	templateEnv = jinja2.Environment( loader=templateLoader )
	TEMPLATE_FILE = "template.j2"
	template = templateEnv.get_template( TEMPLATE_FILE )
	outputText = template.render(groups=groups) # this is where to put args to the template renderer

	return outputText.encode('UTF-8')

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Compositor de datalist para DataProtect",
		epilog="Procesamiento distribuido. Frank@5123 Dic/17")
	# parser.add_argument('-t',
	# 	type=str,
	# 	help='(Opcional) Ruta al archivo de template. Por defecto, utilizara "template.j2" en el directorio local.',
	# 	default="./template.j2",
	# 	dest="template",
	# 	)
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
	parser.add_argument('-i', #Archivo de entrada.
		nargs='?',
		type=str, #String con nombre de archivo de entrada. Antes: argparse.FileType('r'),
		dest='archivoentrada',
		required=True,
		help='Nombre del archivo (JSON) de entrada, generado por el programa dpsourcer.py',
		)
	parser.add_argument('-o', #Archivo de salida. Opcional
		nargs='?',
		type=argparse.FileType('w'),
		default=sys.stdout,
		dest='archivosalida',
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
	

	# logging.info("""Parametros recibidos:
	# 	archivoentrada: {}
	# 	debug: {}
	# 	template: {}
	#	""".format(args.archivoentrada, args.debug, args.template))

	logging.info("""Parametros recibidos:
		archivoentrada: {}
		debug: {}
		""".format(args.archivoentrada, args.debug))

	diccionario = leerJson(args.archivoentrada)
	grupos = componerGrupos(diccionario)
	salida = renderear(grupos)
	# print sys.stdout.encoding
	args.archivosalida.write(salida)
	args.archivosalida.close()
