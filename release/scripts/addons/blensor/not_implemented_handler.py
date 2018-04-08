import bpy

class NotImplemented(object):
    def __getattr__(self, name):
        def method(*args):
            print("tried to handle unknown method " + name)
            bpy.ops.message.nativewarningmessagebox('INVOKE_DEFAULT')
            return None
        return method