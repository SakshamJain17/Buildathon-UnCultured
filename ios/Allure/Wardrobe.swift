import SwiftUI
import PhotosUI

func normalisedPhoto(_ data: Data) throws -> Data {
    guard let image=UIImage(data:data) else {throw AppError(message:"This photo could not be opened.")}
    let scale=min(1,1600/max(image.size.width,image.size.height))
    let size=CGSize(width:image.size.width*scale,height:image.size.height*scale)
    let format=UIGraphicsImageRendererFormat(); format.scale=1
    let rendered=UIGraphicsImageRenderer(size:size,format:format).image {_ in image.draw(in:CGRect(origin:.zero,size:size))}
    guard let jpeg=rendered.jpegData(compressionQuality:0.85) else {throw AppError(message:"Could not prepare this photo.")}; return jpeg
}

struct WardrobeView: View {
    @Environment(AppStore.self) private var store
    @State private var adding=false
    @State private var outfit:[Ranked]=[]
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment:.leading,spacing:22) {
                    SectionHeading(eyebrow:"Less scrolling. More wearing.",title:"Your wardrobe,\nreimagined.")
                    Text("Add clothes you own. Your photos are private to your session and uploaded only when you tap Add.").font(.subheadline).foregroundStyle(.secondary)
                    Button("Add a garment",systemImage:"plus") {adding=true}.buttonStyle(.borderedProminent)
                    if store.wardrobe.isEmpty {ContentUnavailableView("Your style starts here",systemImage:"cabinet",description:Text("A favourite shirt, everyday jeans, go-to shoes. Add a few pieces to begin."))}
                    ForEach(store.wardrobe) {product in HStack {WardrobeThumbnail(product:product); VStack(alignment:.leading) {Text(product.title).font(.headline); Text(product.category ?? "").font(.caption).foregroundStyle(.secondary)}; Spacer(); Button(role:.destructive) {Task {await store.perform {let _:EmptyResult=try await store.api.request("/wardrobe/\(product.id)",method:"DELETE"); try await store.refresh()}}} label: {Image(systemName:"trash")}.accessibilityLabel("Delete "+product.title)}.padding().background(.white,in:RoundedRectangle(cornerRadius:20))}
                    if !store.wardrobe.isEmpty {Button("Build an outfit from my wardrobe",systemImage:"sparkles") {Task {await store.perform {let result:Feed=try await store.api.request("/wardrobe/outfits",method:"POST",body:[:]); outfit=result.items}}}.buttonStyle(.bordered).disabled(store.busy)}
                    ForEach(outfit) {ProductRow(product:$0.product)}
                    if !outfit.isEmpty {Text("Uses your garment labels and preferences. Full colour and fit compatibility are still in development.").font(.caption).foregroundStyle(.secondary)}
                }.padding(24)
            }.background(Theme.paper).navigationTitle("Wardrobe").navigationBarTitleDisplayMode(.inline).sheet(isPresented:$adding) {AddGarmentView()}
        }
    }
}

struct WardrobeThumbnail: View {
    @Environment(AppStore.self) private var store
    let product:Product
    @State private var image:UIImage?
    var body:some View {
        Group {if let image {Image(uiImage:image).resizable().scaledToFill()} else {Image(systemName:product.symbol).font(.title)}}.frame(width:65,height:80).background(Theme.sand.opacity(0.4)).clipShape(RoundedRectangle(cornerRadius:12))
            .task(id:product.id) {if let data=try? await store.api.image(product.id) {image=UIImage(data:data)}}
    }
}

struct AddGarmentView:View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @State private var selection:PhotosPickerItem?
    @State private var data:Data?
    @State private var title=""
    @State private var category="tops"
    @State private var color="neutral"
    @State private var uploading=false
    var body:some View {
        NavigationStack {
            Form {
                Section("Garment photo") {
                    PhotosPicker(selection:$selection,matching:.images) {Label(data == nil ? "Choose a photo" : "Change photo",systemImage:"photo")}
                    if let data,let image=UIImage(data:data) {Image(uiImage:image).resizable().scaledToFit().frame(maxHeight:220)}
                    Text("Only the photo you select is accessible. Adding it uploads a private copy to your backend.").font(.caption).foregroundStyle(.secondary)
                }
                Section("About the piece") {
                    TextField("e.g. My olive overshirt",text:$title)
                    Picker("Category",selection:$category) {ForEach(["tops","bottoms","footwear","one-pieces","accessories"],id:\.self) {Text($0.capitalized).tag($0)}}
                    TextField("Colour",text:$color)
                }
                Button(uploading ? "Adding…" : "Add to my wardrobe") {Task {await upload()}}.disabled(data == nil || title.trimmingCharacters(in:.whitespaces).isEmpty || uploading)
            }.navigationTitle("A piece of you").navigationBarTitleDisplayMode(.inline).toolbar {ToolbarItem(placement:.cancellationAction) {Button("Cancel") {dismiss()}.disabled(uploading)}}
        }.onChange(of:selection) {_,item in Task {do {if let raw=try await item?.loadTransferable(type:Data.self) {data=try normalisedPhoto(raw)}} catch {store.error=error.localizedDescription}}}
    }
    func upload() async {
        guard let data else {return}; uploading=true; defer {uploading=false}
        do {let _:WardrobeCreated=try await store.api.upload("/wardrobe",fields:["title":title,"category":category,"color":color],files:[UploadedFile(field:"image",data:data)]); try await store.refresh(); dismiss()} catch {store.error=error.localizedDescription}
    }
}
