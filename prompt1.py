# import pythoncom
# pythoncom.CoInitialize()

import clr, sys
from System import Array, Environment
from System.IO import Directory, Path

dwsimpath = "/Applications/DWSIM.app/Contents/MonoBundle"
sys.path.append(dwsimpath)

clr.AddReference("DWSIM.Automation")
clr.AddReference("DWSIM.Interfaces")

from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType
from DWSIM.Automation import Automation3

Directory.SetCurrentDirectory(dwsimpath)

manager = Automation3()
sim = manager.CreateFlowsheet()

# === COMPONENTS ===
cnames = ["Nitrogen", "Hydrogen", "Ammonia"]
for c in cnames:
    sim.AddCompound(c)

# === PROPERTY METHOD ===
pp = sim.CreateAndAddPropertyPackage("NRTL")  # or PR, SRK etc.

# === UNIT OPERATIONS ===
feed_obj      = sim.AddObject(ObjectType.MaterialStream, 50, 200, "Fresh_Feed")
mixer_obj     = sim.AddObject(ObjectType.Mixer, 200, 200, "Mixer")
reactor_obj   = sim.AddObject(ObjectType.RCT_Gibbs, 400, 200, "Gibbs")  # simulate reaction
sep_obj       = sim.AddObject(ObjectType.ComponentSeparator, 600, 200, "Sep")
splitter_obj  = sim.AddObject(ObjectType.Splitter, 800, 200, "Splitter")

# --- INTERMEDIATE STREAMS ---
m1 = sim.AddObject(ObjectType.MaterialStream, 300, 200, "Mixer_to_Reactor")
m2 = sim.AddObject(ObjectType.MaterialStream, 500, 200, "Reactor_to_Sep")
out_nh3 = sim.AddObject(ObjectType.MaterialStream, 600, 100, "Pure_NH3")
out_gas = sim.AddObject(ObjectType.MaterialStream, 750, 200, "Unreacted_Gas")
purge = sim.AddObject(ObjectType.MaterialStream, 950, 150, "Purge")
recycle_out = sim.AddObject(ObjectType.MaterialStream, 950, 250, "Recycle_Stream")

# === CONFIGURE FEED ===
feed = feed_obj.GetAsObject()
feed.SetTemperature(300 + 273.15)     # K
feed.SetPressure(54 * 101325)         # Pa
feed.SetOverallComposition(Array[float]([0.25, 0.75, 0.0]))  # N2/H2/NH3 fractions

# Convert feed molar flow to mol/s from kmol/hr
n2_flow = 100 / 3600  # kmol/hr → mol/s
h2_flow = 300 / 3600
feed.SetMolarFlow(n2_flow + h2_flow)  # total molar flow

# === CONFIGURE REACTOR ===
reactor = reactor_obj.GetAsObject()
reactor.Temperature = 300 + 273.15
reactor.Pressure = 54 * 101325

# === CONNECTIONS ===
sim.ConnectObjects(feed_obj.GraphicObject, mixer_obj.GraphicObject, 0, 0)
sim.ConnectObjects(mixer_obj.GraphicObject, m1.GraphicObject, 0, 0)
sim.ConnectObjects(m1.GraphicObject, reactor_obj.GraphicObject, 0, 0)
sim.ConnectObjects(reactor_obj.GraphicObject, m2.GraphicObject, 0, 0)
sim.ConnectObjects(m2.GraphicObject, sep_obj.GraphicObject, 0, 0)
sim.ConnectObjects(sep_obj.GraphicObject, out_nh3.GraphicObject, 0, 0)  # NH3
sim.ConnectObjects(sep_obj.GraphicObject, out_gas.GraphicObject, 1, 0)   # unreacted gases
sim.ConnectObjects(out_gas.GraphicObject, splitter_obj.GraphicObject, 0, 0)
sim.ConnectObjects(splitter_obj.GraphicObject, purge.GraphicObject, 0, 0)
sim.ConnectObjects(splitter_obj.GraphicObject, recycle_out.GraphicObject, 1, 0)

# === SEPARATOR MATRIX ===
splits = Array.CreateInstance(float, 2, 3)
splits[0, 2] = 1.0  # 100% NH3 to Pure_NH3
splits[1, 0] = 1.0  # 100% N2 to Unreacted_Gas
splits[1, 1] = 1.0  # 100% H2 to Unreacted_Gas
sep_obj.GetAsObject().CompoundSeparationMatrix = splits

# === CALCULATE FLOWSHEET ===
manager.CalculateFlowsheet4(sim)

# === PRINT STREAMS ===
streams = [
    ("Fresh_Feed", feed_obj),
    ("Mixer_to_Reactor", m1),
    ("Reactor_to_Sep", m2),
    ("Pure_NH3", out_nh3),
    ("Unreacted_Gas", out_gas),
    ("Purge", purge),
    ("Recycle_Stream", recycle_out)
]

print("\n=== STREAM FLOW RATES & COMPOSITIONS ===\n")
for name, obj in streams:
    s = obj.GetAsObject()
    mol_flow = s.GetMolarFlow()  # mol/s
    mass_flow = s.GetMassFlow()  # kg/s
    comp = s.GetOverallComposition()

    print(f"Stream: {name}")
    print(f"  Total Molar Flow: {mol_flow*3600:.2f} kmol/hr")  # convert to kmol/hr
    print(f"  Total Mass Flow: {mass_flow*3600:.2f} kg/hr")
    print("  Composition:")
    for i, c in enumerate(cnames):
        print(f"    {c}: {comp[i]:.3f}")
    print("")
