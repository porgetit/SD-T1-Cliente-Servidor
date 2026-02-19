#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import threading
import random

# Diccionario para rastrear clientes: {nombre: socket}
clientes = {}
# Bloqueo para acceso seguro al diccionario desde múltiples hilos
lock = threading.Lock()

def obtener_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def enviar_lista_usuarios(conn):
    with lock:
        lista = ",".join(clientes.keys())
    conn.sendall(f"LIST_USERS:{lista}".encode('utf-8'))

def handle_client(conn, addr, nombre):
    print(f"[NUEVA CONEXIÓN] {nombre} ({addr}) conectado.")
    
    # Notificar al cliente su nombre asignado
    conn.sendall(f"ASSIGN_NAME:{nombre}".encode('utf-8'))
    
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            mensaje_raw = data.decode('utf-8')
            
            if mensaje_raw == "GET_USERS":
                enviar_lista_usuarios(conn)
            
            elif mensaje_raw.startswith("CHAT:"):
                # Formato: CHAT:<destino>:<mensaje>
                try:
                    _, destino, msg = mensaje_raw.split(":", 2)
                    with lock:
                        if destino in clientes:
                            target_sock = clientes[destino]
                            target_sock.sendall(f"FROM:{nombre}:{msg}".encode('utf-8'))
                        else:
                            conn.sendall(f"ERROR:Usuario {destino} no encontrado".encode('utf-8'))
                except ValueError:
                    conn.sendall("ERROR:Formato de mensaje inválido".encode('utf-8'))
            
    except Exception as e:
        print(f"[ERROR] {nombre}: {e}")
    finally:
        with lock:
            if nombre in clientes:
                del clientes[nombre]
        print(f"[DESCONEXIÓN] {nombre} desconectado.")
        conn.close()

def main():
    host = obtener_ip_local()
    port = 0

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen()

    host_real, port_real = sock.getsockname()
    print("="*45)
    print(f"  Servidor de Chat Centralizado listo.")
    print(f"  IP   : {host_real}")
    print(f"  Puerto: {port_real}")
    print("="*45)

    while True:
        conn, addr = sock.accept()
        nombre = f"User_{random.randint(1000, 9999)}"
        
        with lock:
            clientes[nombre] = conn
            
        thread = threading.Thread(target=handle_client, args=(conn, addr, nombre))
        thread.start()
        print(f"[CONEXIONES ACTIVAS] {len(clientes)}")

if __name__ == "__main__":
    main()
