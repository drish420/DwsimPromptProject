import sys
import os
import pythonnet
import logging

if not pythonnet.get_runtime_info():
    pythonnet.load("mono")

import clr
from mcp.server.fastmcp import FastMCP

# Path setup for macOS
dwsim_path = "/Applications/DWSIM.app/Contents/MonoBundle"
sys.path.append(dwsim_path)

# Load DWSIM Libraries
clr.AddReference("DWSIM.Automation")
clr.AddReference("DWSIM.Interfaces")
clr.AddReference("DWSIM.Thermodynamics")
clr.AddReference("DWSIM.UnitOperations")

from DWSIM.Automation import Automation3
from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType

# -------------------- MCP Server --------------------
mcp = FastMCP("DWSIM_Builder")
interf = Automation3()
sim = None

# ---------- Core Tools ----------

@mcp.tool()
def start_new_flowsheet() -> str:
    """Initializes a fresh, empty simulation flowsheet."""
    global sim
    sim = interf.CreateFlowsheet()
    return "New flowsheet initialized."

@mcp.tool()
def add_compound(name: str) -> str:
    """Adds a chemical compound to the simulation."""
    if not sim: return "Error: Start a flowsheet first."
    if name in sim.AvailableCompounds:
        comp = sim.AvailableCompounds[name]
        sim.SelectedCompounds.Add(comp.Name, comp)
        return f"Added {name} to selected compounds."
    return f"Compound {name} not found in DWSIM database."

@mcp.tool()
def add_property_package(type_name: str) -> str:
    """Sets the thermodynamic model. Options: 'NRTL', 'Peng-Robinson', 'SteamTables'."""
    if not sim: return "Error: Start a flowsheet first."
    package = sim.CreateAndAddPropertyPackage(type_name)
    return f"Property Package '{type_name}' added successfully."

@mcp.tool()
def add_unit_op(obj_type: str, name: str) -> str:
    """Adds equipment: MaterialStream, Heater, Pump, Valve."""
    if not sim: return "Error: Start a flowsheet first."
    type_map = {
        "MaterialStream": ObjectType.MaterialStream,
        "Heater": ObjectType.Heater,
        "Pump": ObjectType.Pump,
        "Valve": ObjectType.OT_Valve
    }
    if obj_type in type_map:
        sim.AddObject(type_map[obj_type], 100, 100, name)
        return f"Added {obj_type} named '{name}'."
    return f"Unknown object type: {obj_type}."

@mcp.tool()
def connect_units(from_obj: str, to_obj: str) -> str:
    """Connects two objects (e.g., stream to pump)."""
    obj1 = sim.GetFlowsheetSimulationObject(from_obj)
    obj2 = sim.GetFlowsheetSimulationObject(to_obj)
    sim.ConnectObjects(obj1.GraphicObject, obj2.GraphicObject, -1, -1)
    return f"Connected {from_obj} to {to_obj}."

# ---------- New Tools ----------

@mcp.tool()
def set_heater(stream_in: str, stream_out: str, target_temp: float) -> str:
    """Adds/configures a heater and sets outlet temperature."""
    global sim
    if not sim: return "Error: Start a flowsheet first."
    heater_name = f"Heater_{stream_in}_to_{stream_out}"
    sim.AddObject(ObjectType.Heater, 100, 100, heater_name)
    heater = sim.GetFlowsheetSimulationObject(heater_name)
    inlet = sim.GetFlowsheetSimulationObject(stream_in)
    outlet = sim.GetFlowsheetSimulationObject(stream_out)
    sim.ConnectObjects(inlet.GraphicObject, heater.GraphicObject, -1, -1)
    sim.ConnectObjects(heater.GraphicObject, outlet.GraphicObject, -1, -1)
    heater.GraphicObject.SetProperty("TargetTemperature", target_temp)
    return f"Heater {heater_name} set from {stream_in} to {stream_out} at {target_temp} °C"

@mcp.tool()
def generate_txy(components: list, pressure: float, num_points: int = 50) -> str:
    """Creates a Txy diagram for given components at specified pressure."""
    global sim
    if not sim: return "Error: Start a flowsheet first."
    txy_name = "_".join(components) + "_Txy"
    sim.AddObject(ObjectType.TxyDiagram, 100, 200, txy_name)
    txy = sim.GetFlowsheetSimulationObject(txy_name)
    txy.GraphicObject.SetProperty("Components", components)
    txy.GraphicObject.SetProperty("Pressure", pressure)
    txy.GraphicObject.SetProperty("NumPoints", num_points)
    return f"Txy diagram {txy_name} created for {components} at {pressure} bar"

@mcp.tool()
def run_simulation() -> str:
    """Solves the current flowsheet headlessly."""
    global sim
    if not sim: return "Error: Start a flowsheet first."
    try:
        sim.Solve()
        return "Simulation completed successfully."
    except Exception as e:
        return f"Simulation failed: {e}"

@mcp.tool()
def get_stream_value(stream_name: str, property_name: str) -> str:
    """Returns a property (e.g., Temperature, HeatDuty) of a stream."""
    global sim
    if not sim: return "Error: Start a flowsheet first."
    stream = sim.GetFlowsheetSimulationObject(stream_name)
    try:
        value = stream.GraphicObject.GetProperty(property_name)
        return value
    except Exception as e:
        return f"Failed to get {property_name} for {stream_name}: {e}"

@mcp.tool()
def save_to_desktop(filename: str) -> str:
    """Saves flowsheet to macOS Desktop."""
    global sim
    if not sim: return "Error: Start a flowsheet first."
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
    sim.SaveSimulation(desktop_path)
    return f"Flowsheet saved to {desktop_path}"

# ---------- Run MCP server ----------
if __name__ == "__main__":
    mcp.run()