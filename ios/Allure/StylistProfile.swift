import SwiftUI
import PhotosUI

struct StylistView:View {
    @Environment(AppStore.self) private var store
    @State private var prompt=""
    @State private var run:Run?
    @State private var chatting=false
    @State private var previousRun:String?
    @State private var showAdd=false
    @State private var showTryOn=false
    @State private var showAvatar=false
    @State private var actionProduct:Product?
    @Environment(\.dismiss) private var dismiss
    var body:some View {
        NavigationStack {
            ScrollView {
                VStack(alignment:.leading,spacing:24) {
                    Text("What can I do for you?").font(.system(size:31,design:.serif))
                    Text("I can find outfits, save pieces, update your preferences, and show your progress.").font(.subheadline).foregroundStyle(.secondary)
                    ForEach(["Save this piece for me.","Show my wardrobe and style progress."],id:\.self) {suggestion in Button {prompt=suggestion} label: {HStack {Text(suggestion).font(.subheadline).multilineTextAlignment(.leading); Spacer(); Image(systemName:"arrow.up.left")}.padding().background(.white,in:RoundedRectangle(cornerRadius:16))}}
                    TextField("Ask ALLURÉ…",text:$prompt,axis:.vertical).lineLimit(3...6).padding().background(.white,in:RoundedRectangle(cornerRadius:18))
                    Button(chatting ? "Your stylist is thinking…" : "Ask my stylist",systemImage:"sparkles") {Task {await ask()}}.buttonStyle(.borderedProminent).disabled(prompt.trimmingCharacters(in:.whitespaces).count<2 || chatting)
                    if chatting {HStack {OrbCluster().frame(width:70,height:65);Text("Thinking…").font(.subheadline).foregroundStyle(.secondary)}}
                    if let run {
                        Text(run.answer).textSelection(.enabled).lineSpacing(5)
                        Label(run.status.replacingOccurrences(of:"_",with:" ").capitalized,systemImage:run.status == "completed" ? "checkmark.circle" : "info.circle").font(.caption).foregroundStyle(.secondary)
                        DisclosureGroup("Tools used · \(run.trace.count)") {ForEach(run.trace) {event in HStack {Text(event.tool.replacingOccurrences(of:"_",with:" ")); Spacer(); Text(event.status)}.font(.caption).padding(.vertical,4)}}
                        ForEach(run.products) {ProductRow(product:$0)}
                    }
                    Text("Powered by your configured model. Tool results are the evidence; generated advice can be imperfect. Demo products are not merchant listings.").font(.caption).foregroundStyle(.secondary)
                }.padding(24)
            }.background(Theme.paper).navigationTitle("").toolbar {ToolbarItem(placement:.principal) {BrandLockup(size:26)}}.navigationBarTitleDisplayMode(.inline).toolbar {Button("Done") {dismiss()}}
            .task {if !store.assistantDraft.isEmpty {prompt=store.assistantDraft;store.assistantDraft="";if store.assistantAutoSend {store.assistantAutoSend=false;await ask()}}}
            .sheet(isPresented:$showAdd) {AddGarmentView()}
            .sheet(isPresented:$showTryOn) {TryOnView(selectedProduct:actionProduct)}
            .sheet(isPresented:$showAvatar) {StyleAvatarView()}
        }
    }
    func ask() async {
        chatting=true; defer {chatting=false}
        var body:[String:Any]=["message":prompt]; if let location=store.location {body["location"]=location}; if let previousRun {body["previous_run_id"]=previousRun};if let selected=store.focusedProductID ?? store.feed.first?.product.id {body["selected_product_id"]=selected}
        do {let result:Run=try await store.api.request("/agent/shop",method:"POST",body:body); run=result; previousRun=result.runId;try await store.applyBotActions(result.uiActions ?? []);for action in result.uiActions ?? [] where action.type == "open_feature" {switch action.feature {case "upload_garment":showAdd=true;case "tryon":actionProduct=result.products.first(where:{$0.id==action.productId});showTryOn=true;case "avatar":showAvatar=true;default:break}};if (result.uiActions ?? []).contains(where:{$0.type=="open_feature" && ["discover","wardrobe","saved","profile","analyze_style","palette","hair"].contains($0.feature ?? "")}) {dismiss()}} catch {store.error=error.localizedDescription}
    }
}

struct ProfileView:View {
    @Environment(AppStore.self) private var store
    @State private var aesthetic="minimalist"
    @State private var colors="beige, olive"
    @State private var fit="relaxed"
    @State private var inspiration=""
    @State private var tags=""
    @State private var selectedPhotos:[PhotosPickerItem]=[]
    @State private var analysisMessage=""
    @State private var analysing=false
    @State private var showHair=false
    @State private var showPalette=false
    @State private var confirmDelete=false
    @State private var photosOpen=false
    var body:some View {NavigationStack {Form {
        Section {
            Text(store.name).font(.system(size:33,design:.serif))
            Text("Your style passport.").font(.subheadline).foregroundStyle(.secondary)
            HStack {stat("Likes",store.insights?.interactions["like"] ?? 0);Spacer();stat("Saved",store.insights?.savedCount ?? store.insights?.interactions["save"] ?? 0);Spacer();stat("Passed",store.insights?.interactions["dislike"] ?? 0);Spacer();stat("Pieces",store.insights?.wardrobeCount ?? 0)}.padding(.vertical,8)
        }
        Section {
            DisclosureGroup("Your style") {
                Picker("Aesthetic",selection:$aesthetic) {ForEach(["minimalist","streetwear","smart_casual","casual","contemporary"],id:\.self){Text($0.replacingOccurrences(of:"_",with:" ").capitalized).tag($0)}}
                TextField("Colours, separated by commas",text:$colors)
                Picker("Fit",selection:$fit) {ForEach(["relaxed","oversized","regular","straight"],id:\.self){Text($0.capitalized).tag($0)}}
                Button("Save preferences") {Task {await store.savePreferences(aesthetic:aesthetic,colors:colors,fit:fit)}}.disabled(store.busy)
            }
            DisclosureGroup("Five photo references",isExpanded:$photosOpen) {
                PhotosPicker(selection:$selectedPhotos,maxSelectionCount:5,matching:.images) {Label("Choose five outfit references",systemImage:"photo.on.rectangle")}
                Text("\(selectedPhotos.count) of 5 selected").font(.caption)
                Button(analysing ? "Reading your references…" : "Analyse with AI") {Task {await analyse()}}.disabled(selectedPhotos.count != 5 || analysing)
                if !analysisMessage.isEmpty {Text(analysisMessage).font(.caption)}
                Text("Only selected photos are uploaded. The model analyses clothing, not sensitive personal traits.").font(.caption).foregroundStyle(.secondary)
            }
            DisclosureGroup("People who inspire you") {
                TextField("Creator or celebrity name",text:$inspiration);TextField("Style cues, e.g. streetwear",text:$tags)
                Button("Follow inspiration") {Task {await store.follow(inspiration,tags:tags);if store.error == nil {inspiration="";tags=""}}}.disabled(inspiration.isEmpty || tags.isEmpty || store.busy)
                ForEach(store.inspirations) {item in HStack {Text(item.name);Spacer();Button("Unfollow") {Task {await store.updateInspirations(store.inspirations.filter{$0.id != item.id})}}.font(.caption)}}
                Text("Your chosen cues, not a live celebrity feed or endorsement.").font(.caption).foregroundStyle(.secondary)
            }
            Button("Explore a colour palette",systemImage:"paintpalette") {showPalette=true}
            Button("Explore hairstyles",systemImage:"scissors") {showHair=true}
        }
        Section {
            Button("Guided walkthrough",systemImage:"play.circle") {store.showWalkthrough=true}
            Button("Load labelled sample data",systemImage:"square.stack") {Task {await store.loadSample()}}.disabled(store.busy)
            Text("Sample pieces and sample interactions are illustrative; they don’t represent your own purchases or taste.").font(.caption).foregroundStyle(.secondary)
        }
        Section {
            DisclosureGroup("Privacy & connection") {
                Text(store.endpoint).font(.caption.monospaced())
                Text("Only selected photos and one-time, opt-in location. Prototype sessions are not recoverable accounts.").font(.caption).foregroundStyle(.secondary)
                Button("Sign out") {store.signOut()}
                Button("Delete profile and wardrobe",role:.destructive) {confirmDelete=true}
            }
        }
    }.navigationTitle("").toolbar {ToolbarItem(placement:.principal) {BrandLockup(size:26)}}.navigationBarTitleDisplayMode(.inline)
    .sheet(isPresented:$showHair) {HairView()}.sheet(isPresented:$showPalette) {PaletteView()}
    .confirmationDialog("Delete your profile and private wardrobe photos?",isPresented:$confirmDelete,titleVisibility:.visible) {Button("Delete profile",role:.destructive) {Task {await store.perform {let _:EmptyResult=try await store.api.request("/me",method:"DELETE");store.signOut()}}}}
    .onAppear {aesthetic=store.preferences?.aesthetics?.first ?? "minimalist";colors=store.preferences?.preferredColors?.joined(separator:", ") ?? "beige, olive";fit=store.preferences?.silhouettes?.first ?? "relaxed";openTarget()}
    .onChange(of:store.profileTarget) {_,_ in openTarget()}
    }}
    func stat(_ title:String,_ value:Int)->some View {VStack(alignment:.leading,spacing:5){Text("\(value)").font(.system(size:25,design:.serif));Text(title).font(.system(size:9)).foregroundStyle(.secondary)}}
    func openTarget(){if store.profileTarget=="analyze_style"{photosOpen=true};if store.profileTarget=="hair"{showHair=true};if store.profileTarget=="palette"{showPalette=true};store.profileTarget=nil}
    func analyse() async {
        analysing=true; defer {analysing=false}
        do {
            var files:[UploadedFile]=[]
            for item in selectedPhotos {guard let raw=try await item.loadTransferable(type:Data.self) else {throw AppError(message:"A selected photo could not load.")}; files.append(UploadedFile(field:"images",data:try normalisedPhoto(raw)))}
            let _:EmptyResult=try await store.api.upload("/style/analyze",fields:[:],files:files)
            try await store.refresh(); analysisMessage="Your clothing references have been analysed. Review your preferences above."
        } catch {store.error=error.localizedDescription}
    }
}

struct HairView:View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @State private var length="medium"
    @State private var texture="unsure"
    @State private var goal="Low-maintenance everyday styling"
    @State private var advice=""
    @State private var working=false
    var body:some View {
        NavigationStack {Form {
            Section("Your hair, your choices") {
                Picker("Length",selection:$length) {ForEach(["short","medium","long"],id:\.self) {Text($0.capitalized).tag($0)}}
                Picker("Texture",selection:$texture) {ForEach(["straight","wavy","curly","coily","unsure"],id:\.self) {Text($0.capitalized).tag($0)}}
                TextField("What would you like?",text:$goal,axis:.vertical)
                Button(working ? "Thinking…" : "Suggest hairstyles") {Task {working=true; defer{working=false}; do {let result:Advice=try await store.api.request("/stylist/hair",method:"POST",body:["length":length,"texture":texture,"goal":goal]); advice=result.advice} catch {store.error=error.localizedDescription}}}.disabled(working)
            }
            if !advice.isEmpty {Section("Your styling ideas") {Text(advice).textSelection(.enabled)}}
            Section {Text("Suggestions use the choices you enter. No face-shape, medical, or photo-based analysis is performed.").font(.caption).foregroundStyle(.secondary)}
        }.navigationTitle("A fresh direction").navigationBarTitleDisplayMode(.inline).toolbar {Button("Done") {dismiss()}}}
    }
}

struct PaletteView:View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @State private var undertone="unsure"
    @State private var consent=false
    @State private var palette:Palette?
    var body:some View {
        NavigationStack {Form {
            Section("Explore, don’t restrict") {
                Picker("Your selected undertone",selection:$undertone) {ForEach(["warm","cool","neutral","unsure"],id:\.self) {Text($0.capitalized).tag($0)}}
                Toggle("I want undertone-based colour suggestions",isOn:$consent)
                Button("Explore my palette") {Task {await store.perform {palette=try await store.api.request("/style/palette",method:"POST",body:["undertone":undertone,"consent":true])}}}.disabled(!consent || store.busy)
            }
            if let palette {Section {ForEach(palette.colors) {item in HStack {Circle().fill(Color(hex:item.hex)).frame(width:32,height:32);Text(item.name.capitalized)}}; Text(palette.explanation).font(.caption)}}
            Section {Text("Subjective colour inspiration based on your own selection. We don’t estimate your skin tone from photos or forbid any colours.").font(.caption).foregroundStyle(.secondary)}
        }.navigationTitle("Your colours").toolbar {Button("Done") {dismiss()}}}
    }
}

extension Color {
    init(hex:String) {let value=UInt64(hex.replacingOccurrences(of:"#",with:""),radix:16) ?? 0; self.init(red:Double((value>>16)&255)/255,green:Double((value>>8)&255)/255,blue:Double(value&255)/255)}
}
