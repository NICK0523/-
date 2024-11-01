#Material assignment
for Geo in Model.Geometry.GetChildren(DataModelObjectCategory.Body, True):
    #Geo=Assemble.Children[0]
    if 'ValveBody' in Geo.Name or 'flange' in Geo.Name:
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
pressws[0].Operator=SelectionOperatorType.Equal
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
SealBody=DataModel.GetObjectsByName("seal")
SealGeobody=SealBody[0].GetGeoBody()
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
    if Geo.Name in ['bolt','nut1']:
        sel.Entities=[Geo.GetGeoBody()]
        selmgr.AddSelection(sel)

mesh=Model.Mesh
mesh.ElementSize=Quantity("5 [mm]")
meshsizing=mesh.AddSizing()
meshsizing.ElementSize=Quantity("2 [mm]")
selmgr.ClearSelection()
mesh.GenerateMesh()

#Suppressed reduntant connections
ContactGP=Model.Connections.Children[0]
for connection in ContactGP.Children:
    if (connection.Name).Contains('flange To bolt'):
        connection.Suppressed=True
        
# Analysis settings
Analysis=Model.Analyses[0]
for NS in Model.NamedSelections.Children:
    if (NS.Name).Contains('Fixed'):
        Fixedsupport=Analysis.AddFixedSupport()
        Fixedsupport.Location=NS

Pressure=Analysis.AddPressure()
Pressure.Location=Sealsel
Pressure.Magnitude.Output.SetDiscreteValue(0,Quantity("20 [MPa]"))

Analysis.Solve(True)

#PostProcessing
result=Analysis.Solution.AddTotalDeformation() 
result.EvaluateAllResults()
result=Analysis.Solution.AddEquivalentStress()
result.DisplayTime=Quantity("1 [sec]")
result.EvaluateAllResults()
result.Maximum
