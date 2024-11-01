import os
from ansys.mechanical.core import launch_mechanical
from matplotlib import image as mpimg
from matplotlib import pyplot as plt

geometry_path = r'D:\PyMAPDL\PyMechanical\Demo\78M.sat' 
mat_path = r'D:\PyMAPDL\PyMechanical\Demo\910M.xml'

mechanical = launch_mechanical(batch=False, cleanup_on_exit=False,version="232")
print(mechanical)

project_directory = mechanical.project_directory
print(f"project directory = {project_directory}")

# Upload the geo & MAT file to the project directory.
mechanical.upload(file_name=geometry_path, file_location_destination=project_directory)
mechanical.upload(file_name=mat_path, file_location_destination=project_directory)
#
## Build the geo path relative to project directory.  建立相對於專案目錄的路徑 ## 這邊看不懂可用chatgpt查很清楚
base_name = os.path.basename(geometry_path)
print(base_name)
combined_path = os.path.join(project_directory, base_name)
print(combined_path)
part_file_path = combined_path.replace("\\", "\\\\")
print(part_file_path)
mechanical.run_python_script(f"geometry_path='{part_file_path}'")
#

base_name = os.path.basename(mat_path)
combined_path = os.path.join(project_directory, base_name)
mat_file_path = combined_path.replace("\\", "\\\\")
mechanical.run_python_script(f"mat_file_path='{mat_file_path}'")

## Verify the geo path.
result = mechanical.run_python_script("geometry_path")
print(f"geometry_path on server: {result}")

## Verify the MAT path.
result = mechanical.run_python_script("mat_file_path")
print(f"mat_file_path on server: {result}")

preprocess = mechanical.run_python_script(
    """


# Section 1: Read geometry information
geometry_import_group = Model.GeometryImportGroup
geometry_import = geometry_import_group.AddGeometryImport()
geometry_import_format = (
    Ansys.Mechanical.DataModel.Enums.GeometryImportPreference.Format.Automatic
)
geometry_import_preferences = Ansys.ACT.Mechanical.Utilities.GeometryImportPreferences()
geometry_import_preferences.ProcessNamedSelections = True
geometry_import.Import(
    geometry_path, geometry_import_format, geometry_import_preferences
)
# Import materials.
MAT = ExtAPI.DataModel.Project.Model.Materials
MAT.Import(mat_file_path)

Model.AddStaticStructuralAnalysis()
ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardNMM

#Material assignment
for Geo in Model.Geometry.GetChildren(DataModelObjectCategory.Body, True):
    #Geo=Assemble.Children[0]
    if 'valve' in Geo.Name or 'flange' in Geo.Name:
        Geo.Material='Type 40 Gray Cast Iron'
    elif 'seal' in Geo.Name:
        Geo.Material='Type 302 Stainless Steel'
    else:
        Geo.Material='AISI 6150 Steel'

        
#Create Nameselection by worksheet
for i in range(2):
    NS=Model.AddNamedSelection()
    NS.ScopingMethod=GeometryDefineByType.Worksheet
    NS.Name="Fixed"+str(i)
    NSWS=NS.GenerationCriteria
    NSWS.Add(None)
    NSWS[0].EntityType=SelectionType.GeoFace
    NSWS[0].Criterion=SelectionCriterionType.LocationY
    if i==0:
        NSWS[0].Operator=SelectionOperatorType.Largest
    else:
        NSWS[0].Operator=SelectionOperatorType.Smallest
    NS.Generate()
    
#Pick buttom of Seal worksheet
Nsel=Model.AddNamedSelection()
Nsel.ScopingMethod=GeometryDefineByType.Worksheet
Nsel.Name="Pressure"
pressws=Nsel.GenerationCriteria
pressws.Add(None)
pressws[0].EntityType=SelectionType.GeoBody
pressws[0].Criterion=SelectionCriterionType.Name
pressws[0].Operator=SelectionOperatorType.Contains
pressws[0].Value="seal"
pressws.Add(None)
pressws[1].Action=SelectionActionType.Convert
pressws[1].EntityType=SelectionType.GeoFace
pressws.Add(None)
pressws[2].Action=SelectionActionType.Filter
pressws[2].EntityType=SelectionType.GeoFace
pressws[2].Criterion=SelectionCriterionType.LocationZ
pressws[2].Operator=SelectionOperatorType.LessThanOrEqual
pressws[2].Value=Quantity("65 [mm]")
Nsel.Generate()

#Pick buttom os seal by Geobody 
SealBody=DataModel.GetObjectsByName("Component4.seal")
SealGeobody=SealBody[1].GetGeoBody()
Pressureface=[]
cenZ=1e9
for face in SealGeobody.Faces:
    if face.Centroid[2]<cenZ:
        cenZ=face.Centroid[2]
        Pressureface=face
    print(cenZ)
    
#Selection Manager    
selmgr=ExtAPI.SelectionManager
selmgr.ClearSelection()
Sealsel=selmgr.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
Sealsel.Entities=[Pressureface]
NS=Model.NamedSelections.AddNamedSelection()
NS.Location=Sealsel
NS.Name="Preesure2"

#Mesh sizing
selmgr.ClearSelection()
sel=selmgr.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)
for Geo in Model.Geometry.GetChildren(DataModelObjectCategory.Body, True):
    if 'bolt' in Geo.Name : 
        sel.Entities=[Geo.GetGeoBody()]
        selmgr.AddSelection(sel)

    if 'nut' in Geo.Name :
        sel.Entities=[Geo.GetGeoBody()]
        selmgr.AddSelection(sel)

mesh=Model.Mesh
mesh.ElementSize=Quantity("5 [mm]")
meshsizing=mesh.AddSizing()
meshsizing.ElementSize=Quantity("2 [mm]")
selmgr.ClearSelection()
mesh.GenerateMesh()
        
# Analysis settings

Analysis=Model.Analyses[0]
for NS in Model.NamedSelections.Children:
    if (NS.Name).Contains('Fixed'):
        Fixedsupport=Analysis.AddFixedSupport()
        Fixedsupport.Location=NS

Pressure=Analysis.AddPressure()
Pressure.Location=Sealsel
Pressure.Magnitude.Output.SetDiscreteValue(0,Quantity("20 [MPa]"))

solution = Analysis.Solution
deformation = solution.AddTotalDeformation()
stress = solution.AddEquivalentStress()

# Solve static analysis.
Analysis.Solve(True)
"""
)

output = mechanical.run_python_script(
    """
import json
dir_deformation_details = {
"Minimum": str(deformation.Minimum),
"Maximum": str(deformation.Maximum),
"Average": str(deformation.Average),
}

dir_stress_details = {
"Minimum": str(stress.Minimum),
"Maximum": str(stress.Maximum),
"Average": str(stress.Average),
}


json.dumps(dir_deformation_details)
json.dumps(dir_stress_details)

"""
)
print(output)

mechanical.exit()