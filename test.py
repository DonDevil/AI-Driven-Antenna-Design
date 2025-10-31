from cst.interface import DesignEnvironment
de = DesignEnvironment()
mws = de.new_mws()
print(de.active_project())
print(mws.filename())
print(mws.folder())
