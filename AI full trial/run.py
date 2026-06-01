# run.py
from parapy.gui import display
from engine import Engine

ENGINE = Engine(
    input_file='input_data.xlsx',
    opr=20.0,
    tit=1500.0,
    mass_flow=50.0,
    omega=1000.0,
)

if __name__ == '__main__':
    display(ENGINE)