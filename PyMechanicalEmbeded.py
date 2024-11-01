
import os

from PIL import Image
import ansys.mechanical.core as mech
from ansys.mechanical.core.examples import delete_downloads, download_file
from matplotlib import image as mpimg
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ansys.mechanical.stubs.v241.Ansys as Ansys

app = mech.App(version=241)
app.update_globals(globals())
print(app)

cwd = os.path.join(os.getcwd(), "out")
print(cwd)

def display_image(image_name):
    plt.figure(figsize=(16, 9))
    plt.imshow(mpimg.imread(os.path.join(cwd, image_name)))
    plt.xticks([])
    plt.yticks([])
    plt.axis("off")
    plt.show()
#API is same as Mechanical API
Graphics.Camera.SetSpecificViewOrientation(ViewOrientationType.Iso)
Graphics.Camera.SetFit()
image_export_format = GraphicsImageExportFormat.PNG
settings_720p = Ansys.Mechanical.Graphics.GraphicsImageExportSettings()
settings_720p.Resolution = GraphicsResolutionType.EnhancedResolution
settings_720p.Background = GraphicsBackgroundType.White
settings_720p.Width = 1280
settings_720p.Height = 720
settings_720p.CurrentGraphicsDisplay = False
Graphics.Camera.Rotate(180, CameraAxisType.ScreenY)

geometry_path = r'D:\PyMAPDL\PyMechanical\Demo\78M.sat' 
mat_path = r'D:\PyMAPDL\PyMechanical\Demo\910M.xml'
print(f"Downloaded the geometry file to: {geometry_path}")
print(f"Downloaded the material file to: {mat_path}")


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
print (geometry_import.ObjectState)
# sphinx_gallery_start_ignore
#assert str(geometry_import.ObjectState) == "Solved", "Geometry Import unsuccessful"
# sphinx_gallery_end_ignore

#app.plot()

MAT = Model.Materials
MAT.Import(mat_path)

# sphinx_gallery_start_ignore
#assert str(MAT.ObjectState) == "FullyDefined", "Materials are not defined"
# sphinx_gallery_end_ignore

Model.AddStaticStructuralAnalysis()

app.ExtAPI.Application.ActiveUnitSystem = MechanicalUnitSystem.StandardNMM
#Preprocess are same with Mechanical ACTAPI
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
 
# check point
Graphics.Camera.SetFit()
Graphics.ExportImage(os.path.join(cwd, "mesh.png"), image_export_format, settings_720p)
display_image("mesh.png")
# Analysis settings
Analysis=Model.Analyses[0]
for NS in Model.NamedSelections.Children:
    if 'Fixed' in NS.Name:
        Fixedsupport=Analysis.AddFixedSupport()
        Fixedsupport.Location=NS

Pressure=Analysis.AddPressure()
Pressure.Location=Sealsel
Pressure.Magnitude.Output.SetDiscreteValue(0,Quantity("20 [MPa]"))
# check point
Analysis.Activate()
Graphics.Camera.SetFit()
Graphics.ExportImage(
    os.path.join(cwd, "boundary_conditions.png"), image_export_format, settings_720p
)
display_image("boundary_conditions.png")

solution = Analysis.Solution
deformation = solution.AddTotalDeformation()
stress = solution.AddEquivalentStress()

Analysis.Solve(True)

#Show messages
Messages = ExtAPI.Application.Messages
if Messages:
    for message in Messages:
        print(f"[{message.Severity}] {message.DisplayString}")
else:
    print("No [Info]/[Warning]/[Error] Messages")

#control graphic by tree
Tree.Activate([deformation])
Graphics.ExportImage(
    os.path.join(cwd, "totaldeformation_valve.png"), image_export_format, settings_720p
)
display_image("totaldeformation_valve.png")


Tree.Activate([stress])
Graphics.ExportImage(
    os.path.join(cwd, "stress_valve.png"), image_export_format, settings_720p
)
display_image("stress_valve.png")

#generate animation
animation_export_format = (
    Ansys.Mechanical.DataModel.Enums.GraphicsAnimationExportFormat.GIF
)
settings_720p = Ansys.Mechanical.Graphics.AnimationExportSettings()
settings_720p.Width = 1280
settings_720p.Height = 720

stress.ExportAnimation(
    os.path.join(cwd, "Valve.gif"), animation_export_format, settings_720p
)
gif = Image.open(os.path.join(cwd, "Valve.gif"))
fig, ax = plt.subplots(figsize=(16, 9))
ax.axis("off")
img = ax.imshow(gif.convert("RGBA"))

def update(frame):
    gif.seek(frame)
    img.set_array(gif.convert("RGBA"))
    return [img]


ani = FuncAnimation(
    fig, update, frames=range(gif.n_frames), interval=100, repeat=True, blit=True
)
plt.show()

#show solver output
def write_file_contents_to_console(path):
    """Write file contents to console."""
    with open(path, "rt") as file:
        for line in file:
            print(line, end="")


solve_path = Analysis.WorkingDir
solve_out_path = os.path.join(solve_path, "solve.out")
if solve_out_path:
    write_file_contents_to_console(solve_out_path)

app.print_tree()


app.save(os.path.join(cwd, "valve.mechdat"))
app.new()

