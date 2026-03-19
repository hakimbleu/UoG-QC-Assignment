from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_gate
from qiskit.visualization import array_to_latex
from qiskit.quantum_info import Operator
from qiskit.quantum_info import Statevector
from qiskit import transpile 
from qiskit.providers.basic_provider import BasicSimulator
from qiskit.visualization import plot_histogram
from qiskit.circuit import ControlledGate
import math 
import numpy as np

def alice_measure(qc, qubit, choice):
    if choice == 1:
        qc.ry(-np.pi/2, qubit)
    elif choice == 2:
        qc.ry(-np.pi/4, qubit)

def bob_measure(qc, qubit, choice):
    if choice == 1:
        qc.ry(-np.pi/4, qubit)
    elif choice == 3:
        qc.ry(-3*np.pi/4, qubit)

def quantum_random():
    theta = 2 * np.arccos(1 / np.sqrt(3))

    qc1 = QuantumCircuit(1, 1)
    qc1.ry(theta, 0)
    qc1.measure(0, 0)

    qc2 = QuantumCircuit(1, 1)
    qc2.h(0)
    qc2.measure(0, 0)

    sampler = BasicSimulator()
    result1 = sampler.run(transpile(qc1, sampler), shots=1).result()
    counts1 = result1.get_counts()
    bit1 = int(list(counts1.keys())[0])
    result2 = sampler.run(transpile(qc2, sampler), shots=1).result()
    counts2 = result2.get_counts()
    bit2 = int(list(counts2.keys())[0])
        
    if bit1 == 0:
        choice = 1
    else:
        if bit2 == 0:
            choice = 2
        else:
            choice = 3

    return choice

def attacker_intercept(qc, sampler):
    qc.measure(0, 0)
    qc.measure(1, 1)

    result = sampler.run(transpile(qc, sampler), shots=1).result()
    bits = list(result.get_counts().keys())[0]
    attacker_bit_1 = int(bits[1])
    attacker_bit_2 = int(bits[0])

    intercepted_qc = QuantumCircuit(2, 2)
    if attacker_bit_1 == 1:
        intercepted_qc.x(0)
    if attacker_bit_2 == 1:
        intercepted_qc.x(1)

    return intercepted_qc

def protocol(N, attacker):
    measurements = []
    sampler = BasicSimulator()

    for _ in range(int(9*N/2)):
        qc = QuantumCircuit(2, 2)
        qc.x(0)
        qc.h(0)
        qc.cx(0, 1)
        qc.x(1)

        if attacker:
            qc = attacker_intercept(qc, sampler)

        alice_choice = quantum_random()
        bob_choice = quantum_random()

        alice_measure(qc, 0, alice_choice)
        bob_measure(qc, 1, bob_choice)

        qc.measure(0, 0)
        qc.measure(1, 1)

        result = sampler.run(transpile(qc, sampler), shots=1).result()
        bits = list(result.get_counts().keys())[0]
        alice_bit = int(bits[1])
        bob_bit = int(bits[0])

        measurements.append((alice_choice, alice_bit, bob_choice, bob_bit))

    return measurements

def measurement_parsing(measurements):
    valid_measurements = []
    bell_test_measurements = []
    discarded_measurements = []

    for m in measurements:
        if (m[0] == 2 and m[2] == 1) or (m[0] == 3 and m[2] == 2):
            valid_measurements.append(m)
        elif (m[0] == 1 and m[2] == 1) or (m[0] == 1 and m[2] == 3) or (m[0] == 3 and m[2] == 1) or (m[0] == 3 and m[2] == 3):
            bell_test_measurements.append(m)
        else:
            discarded_measurements.append(m)

    return valid_measurements, bell_test_measurements, discarded_measurements

def key_builder(valid_measurements):
    alice_key_bits = []
    bob_key_bits = []

    for m in valid_measurements:
        alice_bit = m[1]
        bob_bit = m[3]
        alice_key_bits.append(alice_bit)
        bob_key_bits.append(1- bob_bit)

    return alice_key_bits, bob_key_bits

def bell_test(measurements):
    correlators = {(1,1): [], (1,3): [], (3,1): [], (3,3): []}

    for m in measurements:
        a = 1 - 2 * m[1]
        b = 1 - 2 * m[3]
        correlators[(m[0], m[2])].append(a * b)

    XW = sum(correlators[(1,1)]) / len(correlators[(1,1)]) if correlators[(1,1)] else 0
    XV = sum(correlators[(1,3)]) / len(correlators[(1,3)]) if correlators[(1,3)] else 0
    ZW = sum(correlators[(3,1)]) / len(correlators[(3,1)]) if correlators[(3,1)] else 0
    ZV = sum(correlators[(3,3)]) / len(correlators[(3,3)]) if correlators[(3,3)] else 0

    S = abs(XW + XV + ZW - ZV)

    if S > 2:
        print("Bell inequality violated! S = " + str(S) + " no attacker detected")
    else:
        print("Bell inequality not violated! S = " + str(S) + " possible attacker detected")

    return S