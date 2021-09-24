from adt import ADT

class Tree(ADT):
    Empty()
    Leaf(int)
    Node(left=Tree, right=Tree)


Empty, Leaf, Node = Tree.Empty, Tree.Leaf, Tree.Node

tree = Node(Empty(), Node(Leaf(1), Leaf(2)))


def depth(t: Tree):
    match t:
        case Empty():
            return 0
        case Leaf(_):
            return 1
        case Node(a, b):
            return 1 + max(depth(a), depth(b))

print(tree)
print(depth(tree))