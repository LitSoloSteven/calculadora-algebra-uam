from backend.models.matrix import Matrix
from backend.utils.validators import MatrixValidator
from backend.solvers.linear_systems import GaussSolver

def test_gauss_module():
    print("==================================================")
    print(" PRUEBA DEL MÓDULO BACKEND: ELIMINACIÓN GAUSSIANA ")
    print("==================================================\n")

    # Sistema 3x3 expresado en Matriz Aumentada 3x4:
    #  2x + 1y - 1z =  8
    # -3x - 1y + 2z = -11
    # -2x + 1y + 2z = -3
    raw_data = [
        [ 2.0,  1.0, -1.0,   8.0],
        [-3.0, -1.0,  2.0, -11.0],
        [-2.0,  1.0,  2.0,  -3.0]
    ]

    # 1. Validar dimensiones y datos
    valid_dim, msg1 = MatrixValidator.validate_dimensions(3, 4)
    valid_data, msg2 = MatrixValidator.validate_matrix_data(raw_data, 3, 4)

    if not (valid_dim and valid_data):
        print(f"Error de validación: {msg1} | {msg2}")
        return

    # 2. Instanciar Matriz
    A_aug = Matrix(3, 4, raw_data)
    print("--- MATRIZ ORIGINAL AUMENTADA ---")
    print(A_aug)

    # 3. Resolver con Gauss
    solver = GaussSolver(A_aug)
    result = solver.solve()

    # 4. Mostrar Resultados
    print("--- PASOS DEL ALGORITMO ---")
    for idx, step in enumerate(result["steps"]):
        print(f"\nPaso {idx + 1}: {step['description']}")
        print(step["matrix"])

    print("--------------------------------------------------")
    print(f"Estado del Sistema: {result['status']}")
    print(f"Mensaje: {result['message']}")
    
    if result["solution"]:
        print("\nSolución encontrada:")
        for i, val in enumerate(result["solution"]):
            print(f"  x{i+1} = {val}")

from backend.models.matrix import Matrix
from backend.utils.validators import MatrixValidator
from backend.solvers.linear_systems import GaussSolver

def run_fraction_test():
    # Matriz con fracciones en formato texto
    raw_data_with_strings = [
        [ "2",     "1/3",  "-1",   "8"   ],
        [ "-3/2",  "-1",   "2",    "-11" ],
        [ "-2",    "1",    "2/5",  "-3"  ]
    ]

    print("--- PARSEANDO ENTRADAS CON FRACCIONES ---")
    valid, parsed_data, msg = MatrixValidator.validate_and_parse_raw_matrix(raw_data_with_strings, 3, 4)
    
    if not valid:
        print(f"Error de validación: {msg}")
        return

    print("Matriz parseada con éxito.")
    matrix = Matrix(3, 4, parsed_data)
    solver = GaussSolver(matrix)
    result = solver.solve()

    print("\n--- PASOS DEL ALGORITMO ---")
    for step in result["steps"]:
        print(f"\n-> {step['description']}")
        print(step["matrix"])

if __name__ == "__main__":
    test_gauss_module()
    run_fraction_test()

