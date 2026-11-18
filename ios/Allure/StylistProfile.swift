import SwiftUI
import PhotosUI

struct StylistView:View {
    @Environment(AppStore.self) private var store
    @State private var prompt=""
    @State private var run:Run?
    @State private var chatting=false
    var body:some View {
        NavigationStack {
            ScrollView {
                VStack(alignment:.leading,spacing:24) {
                    SectionHeading(eyebrow:"Your personal stylist",title:"Let’s talk style.")
                    Text("Tell me what’s on your mind. A new outfit, a rainy-day layer, or a different direction.").foregroundStyle(.secondary)
                    ForEach(["Find a minimalist shirt in the demo catalogue. Label fictional examples.","Use my style profile and suggest a new outfit direction."],id:\.self) {suggestion in Button {prompt=suggestion} label: {HStack {Text(suggestion).font(.subheadline).multilineTextAlignment(.leading); Spacer(); Image(systemName:"arrow.up.left")}.padding().background(.white,in:RoundedRectangle(cornerRadius:16))}}
                    TextField("Ask ALLURÉ…",text:$prompt,axis:.vertical).lineLimit(3...6).padding().background(.white,in:RoundedRectangle(cornerRadius:18))
                    Button(chatting ? "Your stylist is thinking…" : "Ask my stylist",systemImage:"sparkles") {Task {await ask()}}.buttonStyle(.borderedProminent).disabled(prompt.trimmingCharacters(in:.whitespaces).count<2 || chatting)
                    if chatting {ProgressView("Checking your style and tools…")}
                    if let run {
                        Text(run.answer).textSelection(.enabled).lineSpacing(5)
                        Label(run.status.replacingOccurrences(of:"_",with:" ").capitalized,systemImage:run.status == "completed" ? "checkmark.circle" : "info.circle").font(.caption).foregroundStyle(.secondary)
                        DisclosureGroup("Tools used · \(run.trace.count)") {ForEach(run.trace) {event in HStack {Text(event.tool.replacingOccurrences(of:"_",with:" ")); Spacer(); Text(event.status)}.font(.caption).padding(.vertical,4)}}
                        ForEach(run.products) {ProductRow(product:$0)}
                    }
                    Text("Powered by your configured model. Tool results are the evidence; generated advice can be imperfect. Demo products are not merchant listings.").font(.caption).foregroundStyle(.secondary)
                }.padding(24)
            }.background(Theme.paper).navigationTitle("ALLURÉ").navigationBarTitleDisplayMode(.inline)
        }
    }
    func ask() async {
        chatting=true; defer {chatting=false}
        var body:[String:Any]=["message":prompt]; if let location=store.location {body["location"]=location}
        do {run=try await store.api.request("/agent/shop",method:"POST",body:body)} catch {store.error=error.localizedDescription}
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
    var body:some View {
        NavigationStack {
            Form {
                Section {VStack(alignment:.leading,spacing:8) {Text(store.name).font(.system(size:34,design:.serif)); Text("Individual by design.").foregroundStyle(.secondary)}}
                Section("Your style DNA") {
                    Picker("Aesthetic",selection:$aesthetic) {ForEach(["minimalist","streetwear","smart_casual","casual","outdoor"],id:\.self) {Text($0.replacingOccurrences(of:"_",with:" ").capitalized).tag($0)}}
                    TextField("Colours, separated by commas",text:$colors)
                    Picker("Fit",selection:$fit) {ForEach(["relaxed","oversized","regular","straight"],id:\.self) {Text($0.capitalized).tag($0)}}
                    Button("Save my preferences") {Task {await store.savePreferences(aesthetic:aesthetic,colors:colors,fit:fit)}}.disabled(store.busy)
                }
                Section("People who inspire you") {
                    TextField("Celebrity or creator’s name",text:$inspiration)
                    TextField("Your chosen style tags, e.g. streetwear",text:$tags)
                    Button("Follow this inspiration") {Task {await store.follow(inspiration,tags:tags); if store.error == nil {inspiration="";tags=""}}}.disabled(inspiration.trimmingCharacters(in:.whitespaces).isEmpty || tags.trimmingCharacters(in:.whitespaces).isEmpty || store.busy)
                    ForEach(store.inspirations) {item in HStack {VStack(alignment:.leading) {Text(item.name); Text(item.tags.joined(separator:", ")).font(.caption).foregroundStyle(.secondary)}; Spacer(); Button("Unfollow") {Task {await store.updateInspirations(store.inspirations.filter{$0.id != item.id})}}.font(.caption)} }
                    Text("You choose the style cues. This is inspiration, not an endorsement or a live feed of their recommendations.").font(.caption).foregroundStyle(.secondary)
                }
                Section("Teach ALLURÉ your taste") {
                    PhotosPicker(selection:$selectedPhotos,maxSelectionCount:5,matching:.images) {Label("Choose five outfit references",systemImage:"photo.on.rectangle.angled")}
                    Text("\(selectedPhotos.count) of 5 selected").font(.caption)
                    Button(analysing ? "Analysing…" : "Analyse selected references") {Task {await analyse()}}.disabled(selectedPhotos.count != 5 || analysing)
                    if !analysisMessage.isEmpty {Text(analysisMessage).font(.caption)}
                    Text("Uploads only these five photos to your configured vision model. No automatic library scanning; a vision model must be configured.").font(.caption).foregroundStyle(.secondary)
                }
                Section("Beyond the outfit") {
                    Button("Explore hairstyles",systemImage:"scissors") {showHair=true}
                    Button("Explore your colour palette",systemImage:"paintpalette") {showPalette=true}
                }
                Section("Privacy & connection") {
                    Text(store.endpoint).font(.caption.monospaced())
                    Text("Location is used only after you ask. Wardrobe uploads are private to this session. Prototype sessions are not verified accounts.").font(.caption).foregroundStyle(.secondary)
                    Button("Sign out") {store.signOut()}
                    Button("Delete my profile and wardrobe",role:.destructive) {confirmDelete=true}
                }
            }.navigationTitle("Your kind of style").navigationBarTitleDisplayMode(.inline)
            .sheet(isPresented:$showHair) {HairView()}.sheet(isPresented:$showPalette) {PaletteView()}
            .confirmationDialog("Delete your profile, wardrobe photos and local backend history?",isPresented:$confirmDelete,titleVisibility:.visible) {Button("Delete profile",role:.destructive) {Task {await store.perform {let _:EmptyResult=try await store.api.request("/me",method:"DELETE"); store.signOut()}}}}
            .onAppear {aesthetic=store.preferences?.aesthetics?.first ?? "minimalist"; colors=store.preferences?.preferredColors?.joined(separator:", ") ?? "beige, olive";fit=store.preferences?.silhouettes?.first ?? "relaxed"}
        }
    }
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
