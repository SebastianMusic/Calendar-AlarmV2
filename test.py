class parent:
    def do_something(self):
        print("I am the parent")
        
class child(parent):
    def do_something_else(self):
        print("I am the child")
        
c = child()
c.do_something()