import SwiftUI
import PhotosUI

struct TryOnView:View {
    var selectedProduct:Product? = nil
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @State private var personItem:PhotosPickerItem?
    @State private var garmentItem:PhotosPickerItem?
    @State private var person:Data?
    @State private var garment:Data?
    @State private var consent=false
    @State private var category="tops"
    @State private var job:TryOnJob?
    @State private var submitting=false
    @State private var submissionKey=UUID().uuidString
    @State private var task:Task<Void,Never>?
    var body:some View {
        NavigationStack {
            Form {
                Section {Text("See the possibility.").font(.system(size:30,design:.serif));Text("A visual preview of a garment on you. It won’t measure physical fit or predict your size.").font(.subheadline).foregroundStyle(.secondary)}
                Section("1 · Your photo") {PhotosPicker(selection:$personItem,matching:.images) {Label("Choose a clear, front-facing photo",systemImage:"person.crop.rectangle")}; preview(person)}
                Section("2 · The garment") {PhotosPicker(selection:$garmentItem,matching:.images) {Label("Choose a garment photo",systemImage:"tshirt")}; preview(garment); Picker("Category",selection:$category) {Text("Top").tag("tops");Text("Bottoms").tag("bottoms");Text("One-piece").tag("one-pieces")}}
                Section {
                    Toggle("I have permission to use both photos for AI generation",isOn:$consent)
                    Text("These images are sent to the configured try-on provider only when you generate. External provider retention policies apply.").font(.caption).foregroundStyle(.secondary)
                    Button(submitting ? "Generating…" : "Generate my preview",systemImage:"sparkles") {task=Task {await generate()}}.disabled(!consent || person == nil || garment == nil || submitting)
                }
                if let job {
                    Section("Fitting room") {
                        Text(job.status?.capitalized ?? "Queued")
                        if let message=job.error?.message {Text(message).foregroundStyle(.red)}
                        if let link=job.generatedImageUrl,let url=URL(string:link) {AsyncImage(url:url) {phase in if let image=phase.image {image.resizable().scaledToFit()} else {ProgressView()}}.frame(minHeight:150)}
                        if let notice=job.notice {Text(notice).font(.caption)}
                    }
                }
                Section {Text("Requires a configured FASHN provider. An unavailable provider will show an error; a sample image is never substituted.").font(.caption).foregroundStyle(.secondary)}
            }.navigationTitle("The fitting room").navigationBarTitleDisplayMode(.inline).toolbar {Button("Done") {task?.cancel();dismiss()}}
        }
        .onChange(of:personItem) {_,item in Task {do {if let raw=try await item?.loadTransferable(type:Data.self) {person=try normalisedPhoto(raw);submissionKey=UUID().uuidString}} catch {store.error=error.localizedDescription}}}
        .onChange(of:garmentItem) {_,item in Task {do {if let raw=try await item?.loadTransferable(type:Data.self) {garment=try normalisedPhoto(raw);submissionKey=UUID().uuidString}} catch {store.error=error.localizedDescription}}}
        .onChange(of:category) {_,_ in submissionKey=UUID().uuidString}
        .task {
            if let product=selectedProduct {
                category=["tops","bottoms","one-pieces"].contains(product.category ?? "") ? product.category! : "tops"
                do {
                    let raw:Data
                    if product.source?.contains("wardrobe") == true {raw=try await store.api.image(product.id)}
                    else if let imageUrl=product.imageUrl,let url=URL(string:imageUrl,relativeTo:URL(string:store.endpoint)) {raw=try await URLSession.shared.data(from:url).0}
                    else {return}
                    garment=try normalisedPhoto(raw)
                } catch {store.error="Choose a garment photo to continue."}
            }
        }
        .onDisappear {task?.cancel()}
    }
    @ViewBuilder func preview(_ data:Data?) -> some View {if let data,let image=UIImage(data:data) {Image(uiImage:image).resizable().scaledToFit().frame(maxHeight:170)}}
    func generate() async {
        guard let person,let garment else {return};submitting=true;defer{submitting=false}
        do {
            let created:TryOnJob=try await store.api.upload("/tryon",fields:["consent":"true","category":category],files:[UploadedFile(field:"person_image",data:person),UploadedFile(field:"garment_image",data:garment)],idempotency:submissionKey)
            job=created
            for _ in 0..<100 {
                try await Task.sleep(for:.seconds(3));try Task.checkCancellation()
                let status:TryOnJob=try await store.api.request("/tryon/\(created.jobId)");job=status
                if status.status == "completed" || status.status == "failed" {return}
            }
            store.error="The provider is taking longer than expected. The job is still retained on the backend."
        } catch is CancellationError {} catch {store.error=error.localizedDescription}
    }
}
