

def wizard_obj_info(obj):
    objname = getattr(obj, "name", "?")
    return "<%s.%s '%s' @ %s>" % (obj.__class__.__module__, obj.__class__.__name__, objname, hex(id(obj)))
