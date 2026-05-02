# Swarm of MeArm Robotic Arms via MQTT Protocol

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![Hardware](https://img.shields.io/badge/Hardware-Raspberry%20Pi%20Pico%20W-red)](https://www.raspberrypi.com/products/raspberry-pi-pico/)
[![Event](https://img.shields.io/badge/Presented%20at-Tech%20Fest-orange)](#acknowledgments)

This repository contains the implementation of a synchronized robotic swarm system using **MeArm** robotic arms. The project focuses on distributed control through the **MQTT** (Publish/Subscribe) protocol, enabling multiple robots to execute complex, synchronized choreographies defined by a central server.

## 🚀 Overview

The system architecture allows a central server to broadcast user-defined instructions to a fleet of robots. Each robot, powered by a **Raspberry Pi Pico W**, subscribes to specific topics to receive and execute movements in real-time, ensuring high-precision synchronization across the swarm.

### Key Features:
* **Real-time Synchronization:** Low-latency command execution via MQTT.
* **Scalable Architecture:** Designed to support multiple robotic agents simultaneously.
* **Custom Choreographies:** Ability to load and execute movement sequences from a `.txt` file.
* **Integrated Simulator:** Includes an HTML-based visualizer for testing logic before hardware deployment.

## 📁 Repository Structure

* `main.py`: Entry point for the robotic arm firmware.
* `PubSub_client.py`: MQTT client logic for the Raspberry Pi Pico W.
* `PubSub_server.py`: Central server script for broadcasting commands.
* `Simulator.html`: Web-based simulation tool for movement validation.
* `coreografia.txt`: Script containing the sequence of synchronized movements.
* `topics.txt`: Configuration file for MQTT topic definitions.

## 🛠️ Tech Stack

* **Languages:** MicroPython (Client), Python (Server), HTML/JS (Simulator).
* **Protocols:** MQTT (Message Queuing Telemetry Transport).
* **Hardware:** Raspberry Pi Pico W, MeArm Robot Kit, Servo Motors.

## 👥 Authors

* **Esteban Riveros** - [@TebanRiveros](https://github.com/TebanRiveros)
* **Julian Gamboa** - [@DarknightNJ](https://github.com/DarknightNJ)

## 🎓 Acknowledgments

This project was developed under the tutelage of **Professor Gerardo Muñoz** and was officially presented at the **Tech Fest** technology festival, representing the **Universidad Distrital Francisco José de Caldas**.
