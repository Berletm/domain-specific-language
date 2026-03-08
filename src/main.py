from parser import *
from visulizer import *
from utils import *

import os

def main() -> None:
    q = read_queries(os.path.join(PTH2EXAMPLES, "correct.txt"))
    w = read_queries(os.path.join(PTH2EXAMPLES, "wrong.txt"))
    
    for i in range(len(q)):
        tokens = tokenize(q[i])
        parser = Parser(tokens)
        root = parser.parse()
        
        visualize(root, f"ast_{i}")

    for i in range(len(w)):
        tokens = tokenize(w[i])
        parser = Parser(tokens)
        try:
            root = parser.parse()
        except SyntaxError as e:
            print(e)
            print()
    

if __name__ == "__main__":
    main()
    