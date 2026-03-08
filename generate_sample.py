import sys
import os
import pythonnet

# 1. Initialize the bridge (Same as your MCP server)
if not pythonnet.get_runtime_info():
    pythonnet.load("mono")

import clr
dwsim_path = "/Applications/DWSIM.app/Contents/MonoBundle"
sys.path.append(dwsim_path)

clr.AddReference("DWSIM.Automation")
clr.AddReference("DWSIM.Interfaces")
clr.AddReference("DWSIM.Thermodynamics")
clr.AddReference("DWSIM.UnitOperations")

from DWSIM.Automation import Automation3
from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType

# 2. Setup the Automation Manager
interf = Automation3()
sim = interf.CreateFlowsheet()

# 3. Add Water and Thermodynamics
water = sim.AvailableCompounds["Water"]
sim.SelectedCompounds.Add(water.Name, water)

from DWSIM.Thermodynamics import PropertyPackages
stables = PropertyPackages.SteamTablesPropertyPackage()
sim.AddPropertyPackage(stables)

# 4. Build the Flowsheet (Inlet -> Heater -> Outlet)
m1 = sim.AddObject(ObjectType.MaterialStream, 50, 50, "Inlet_Water")
m2 = sim.AddObject(ObjectType.MaterialStream, 150, 50, "Outlet_Water")
h1 = sim.AddObject(ObjectType.Heater, 100, 50, "Main_Heater")

m1, m2, h1 = m1.GetAsObject(), m2.GetAsObject(), h1.GetAsObject()

# Connect them
sim.ConnectObjects(m1.GraphicObject, h1.GraphicObject, -1, -1)
sim.ConnectObjects(h1.GraphicObject, m2.GraphicObject, -1, -1)

# 5. Set Parameters
m1.SetTemperature(300.0) # 300 K
m1.SetMassFlow(10.0)     # 10 kg/s
h1.OutletTemperature = 350.0 # Heat to 350 K

# 6. Save the file to your Desktop
desktop_path = os.path.expanduser("~/Desktop/test_simulation.dwxmz")
interf.SaveFlowsheet(sim, desktop_path, True)

print(f"Success! Simple simulation created at: {desktop_path}")