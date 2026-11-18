"""Generate a small dependency-free native Xcode app project from tracked Swift sources."""
from pathlib import Path
import hashlib,re
root=Path(__file__).resolve().parents[1]
def uid(s):return hashlib.sha1(s.encode()).hexdigest()[:24].upper()
existing=(root/'Allure.xcodeproj'/'project.pbxproj').read_text() if (root/'Allure.xcodeproj'/'project.pbxproj').exists() else ''
team_match=re.search(r'DEVELOPMENT_TEAM\s*=\s*([A-Z0-9]+)',existing)
team_setting=('DEVELOPMENT_TEAM='+team_match.group(1)+';') if team_match else ''
objects={}
def obj(name,text):objects[uid(name)]=text;return uid(name)
refs=[];builds=[];resourcebuilds=[]
for p in sorted((root/'Allure').glob('*.swift')):
    ref=obj('ref'+p.name,'{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = "'+p.name+'"; sourceTree = "<group>"; }');refs.append(ref)
    builds.append(obj('build'+p.name,'{isa = PBXBuildFile; fileRef = '+ref+'; }'))
for p in sorted((root/'Allure').glob('*.png')):
    ref=obj('ref'+p.name,'{isa=PBXFileReference;lastKnownFileType=image.png;path="'+p.name+'";sourceTree="<group>";}');refs.append(ref)
    resourcebuilds.append(obj('build'+p.name,'{isa=PBXBuildFile;fileRef='+ref+';}'))
def seq(ids):return '('+','.join(ids)+',)'
product=obj('product','{isa=PBXFileReference; explicitFileType=wrapper.application; path=Allure.app; sourceTree=BUILT_PRODUCTS_DIR;}')
sourcegroup=obj('sourcegroup','{isa=PBXGroup; children='+seq(refs)+';path=Allure;sourceTree="<group>";}')
productgroup=obj('products','{isa=PBXGroup;children='+seq([product])+';name=Products;sourceTree="<group>";}')
rootgroup=obj('rootgroup','{isa=PBXGroup;children='+seq([sourcegroup,productgroup])+';sourceTree="<group>";}')
sources=obj('sources','{isa=PBXSourcesBuildPhase;buildActionMask=2147483647;files='+seq(builds)+';runOnlyForDeploymentPostprocessing=0;}')
frameworks=obj('frameworks','{isa=PBXFrameworksBuildPhase;buildActionMask=2147483647;files=();runOnlyForDeploymentPostprocessing=0;}')
resources=obj('resources','{isa=PBXResourcesBuildPhase;buildActionMask=2147483647;files='+seq(resourcebuilds)+';runOnlyForDeploymentPostprocessing=0;}')
projectconfigs=[];targetconfigs=[]
for config in ['Debug','Release']:
    projectconfigs.append(obj('project'+config,'{isa=XCBuildConfiguration;name='+config+';buildSettings={SDKROOT=iphoneos;IPHONEOS_DEPLOYMENT_TARGET=26.0;CLANG_ENABLE_MODULES=YES;SWIFT_VERSION=5.0;};}'))
    targetconfigs.append(obj('target'+config,'{isa=XCBuildConfiguration;name='+config+';buildSettings={PRODUCT_NAME="$(TARGET_NAME)";PRODUCT_BUNDLE_IDENTIFIER=app.allure.prototype;INFOPLIST_FILE=Allure/Info.plist;GENERATE_INFOPLIST_FILE=NO;TARGETED_DEVICE_FAMILY="1,2";CODE_SIGN_STYLE=Automatic;'+team_setting+'SWIFT_VERSION=5.0;IPHONEOS_DEPLOYMENT_TARGET=26.0;SWIFT_ACTIVE_COMPILATION_CONDITIONS="'+('DEBUG' if config=='Debug' else '')+'";SWIFT_OPTIMIZATION_LEVEL="'+('-Onone' if config=='Debug' else '-O')+'";};}'))
pcl=obj('pcl','{isa=XCConfigurationList;buildConfigurations='+seq(projectconfigs)+';defaultConfigurationIsVisible=0;defaultConfigurationName=Release;}')
tcl=obj('tcl','{isa=XCConfigurationList;buildConfigurations='+seq(targetconfigs)+';defaultConfigurationIsVisible=0;defaultConfigurationName=Release;}')
target=obj('target','{isa=PBXNativeTarget;buildConfigurationList='+tcl+';buildPhases='+seq([sources,frameworks,resources])+';buildRules=();dependencies=();name=Allure;productName=Allure;productReference='+product+';productType="com.apple.product-type.application";}')
project=obj('project','{isa=PBXProject;attributes={LastUpgradeCheck=2720;};buildConfigurationList='+pcl+';compatibilityVersion="Xcode 14.0";developmentRegion=en;hasScannedForEncodings=0;knownRegions=(en,Base);mainGroup='+rootgroup+';productRefGroup='+productgroup+';projectDirPath="";projectRoot="";targets='+seq([target])+';}')
out='// !$*UTF8*$!\n{archiveVersion=1;classes={};objectVersion=56;objects={\n'+'\n'.join(k+' = '+v+';' for k,v in objects.items())+'\n};rootObject='+project+';}\n'
(root/'Allure.xcodeproj'/'project.pbxproj').write_text(out)
