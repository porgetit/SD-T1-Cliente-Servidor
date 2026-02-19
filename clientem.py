#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import threading
import sys

# Variables globales para rastrear el estado del chat
solicitud_pendiente_de = None
mi_nombre = None
destino = None

def receive_messages(sock):
    """Hilo para recibir mensajes del servidor de forma asíncrona."""
    global solicitud_pendiente_de, mi_nombre
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            
            mensaje = data.decode('utf-8')
            
            if mensaje.startswith("ASSIGN_NAME:"):
                mi_nombre = mensaje.split(":")[1]
                print(f"\n[SISTEMA] Tu nombre es: {mi_nombre}")
                print("> ", end="", flush=True)
            
            elif mensaje.startswith("LIST_USERS:"):
                usuarios = mensaje.split(":")[1]
                print(f"\n[USUARIOS CONECTADOS] {usuarios}")
                print("> ", end="", flush=True)
            
            elif mensaje.startswith("REQ_CHAT_FROM:"):
                solicitud_pendiente_de = mensaje.split(":")[1]
                print(f"\n[SOLICITUD] {solicitud_pendiente_de} quiere chatear contigo. Escribe 'accept' o 'deny'.")
                print("> ", end="", flush=True)
            
            elif mensaje.startswith("CHAT_ACCEPTED:"):
                usuario = mensaje.split(":")[1]
                print(f"\n[SISTEMA] Chat con {usuario} ESTABLECIDO. Ya puedes enviar mensajes.")
                print("> ", end="", flush=True)
            
            elif mensaje.startswith("CHAT_DENIED:"):
                usuario = mensaje.split(":")[1]
                print(f"\n[SISTEMA] {usuario} ha rechazado tu solicitud de chat.")
                print("> ", end="", flush=True)
            
            elif mensaje.startswith("CHAT_STOPPED:"):
                usuario = mensaje.split(":")[1]
                print(f"\n[SISTEMA] {usuario} ha finalizado el chat.")
                if destino == usuario:
                    destino = None
                print("> ", end="", flush=True)

            elif mensaje.startswith("FROM:"):
                _, remitente, contenido = mensaje.split(":", 2)
                print(f"\n[{remitente}] dice: {contenido}")
                print("> ", end="", flush=True)
            
            elif mensaje.startswith("ERROR:"):
                print(f"\n[ERROR] {mensaje.split(':', 1)[1]}")
                print("> ", end="", flush=True)
                
        except Exception:
            break
    print("\n[DESCONECTADO] Conexión perdida con el servidor.")

def main():
    global solicitud_pendiente_de, destino
    print("="*45)
    host = input("  Ingrese la IP del servidor  : ").strip()
    port = int(input("  Ingrese el puerto del servidor: ").strip())
    print("="*45)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except Exception as e:
        print(f"Error al conectar: {e}")
        return

    # Iniciar hilo de recepción
    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    print("\n--- MENÚ DE CHAT (Confirmación Activada) ---")
    print("Comandos:")
    print("  'list'         - Ver usuarios conectados")
    print("  'chat:<user>'  - Solicitar chat con un usuario")
    print("  'accept'       - Aceptar solicitud entrante")
    print("  'deny'         - Rechazar solicitud entrante")
    print("  'stop'         - Terminar chat actual")
    print("  'exit'         - Salir")
    print("="*45)

    destino = None

    while True:
        try:
            line = input("> ").strip()
            if not line:
                continue
            
            if line == 'exit':
                break
            elif line == 'list':
                sock.sendall("GET_USERS".encode('utf-8'))
            elif line == 'accept':
                if solicitud_pendiente_de:
                    sock.sendall(f"ACCEPT_CHAT:{solicitud_pendiente_de}".encode('utf-8'))
                    destino = solicitud_pendiente_de
                    solicitud_pendiente_de = None
                else:
                    print("[!] No tienes ninguna solicitud pendiente.")
            elif line == 'deny':
                if solicitud_pendiente_de:
                    sock.sendall(f"DENY_CHAT:{solicitud_pendiente_de}".encode('utf-8'))
                    print(f"[INFO] Solicitud de {solicitud_pendiente_de} rechazada.")
                    solicitud_pendiente_de = None
                else:
                    print("[!] No tienes ninguna solicitud pendiente.")
            elif line == 'stop':
                if destino:
                    sock.sendall(f"STOP_CHAT:{destino}".encode('utf-8'))
                    print(f"[INFO] Chat con {destino} finalizado.")
                    destino = None
                else:
                    print("[!] No hay ningún chat activo.")
            elif line.startswith("chat:"):
                destino_tmp = line.split(":", 1)[1]
                if destino_tmp == mi_nombre:
                    print("[!] No puedes chatear contigo mismo.")
                else:
                    sock.sendall(f"REQ_CHAT:{destino_tmp}".encode('utf-8'))
                    print(f"[SISTEMA] Solicitud de chat enviada a {destino_tmp}. Esperando confirmación...")
                    destino = destino_tmp # Asignamos temporalmente, el server validará el relay
            else:
                if destino:
                    sock.sendall(f"CHAT:{destino}:{line}".encode('utf-8'))
                else:
                    print("[!] Debes seleccionar un destinatario primero con 'chat:<nombre>'")
        except KeyboardInterrupt:
            break

    sock.close()

if __name__ == "__main__":
    main()
