import SwiftUI
import WebKit

struct ProductDetailView:View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    let product:Product
    @State private var complements:[Ranked]=[]
    @State private var tryOn=false
    @State private var assistant=false
    var body:some View {
        NavigationStack {
            ScrollView {
                VStack(alignment:.leading,spacing:24) {
                    ProductArtwork(product:product,height:470)
                    VStack(alignment:.leading,spacing:20) {
                        Text((product.category ?? "THE PERSONAL EDIT").uppercased()).font(.system(size:9)).tracking(2)
                        Text(product.title).font(.system(size:35,design:.serif))
                        Text(product.priceText).font(.system(size:10)).foregroundStyle(.secondary)
                        Text((product.colors ?? []).map{$0.capitalized}.joined(separator:" / ")).font(.caption).foregroundStyle(.secondary)
                        Divider()
                        Text("Considered for you.").font(.system(size:25,design:.serif))
                        Text("Explore this piece alongside your preferences. Catalogue colours and aesthetic tags are estimates, not verified merchant attributes.").font(.subheadline).foregroundStyle(.secondary)
                        Button {tryOn=true} label:{HStack {Text("PREVIEW IT ON ME");Spacer();Image(systemName:"arrow.up.right")}.font(.system(size:11)).tracking(1).padding(12).frame(maxWidth:.infinity)}.buttonStyle(.borderedProminent)
                        Button("Ask Allure about this piece",systemImage:"sparkles") {store.focusedProductID=product.id;assistant=true}.font(.subheadline)
                        if product.source?.contains("wardrobe") != true {
                            HStack {Button("Save",systemImage:"bookmark") {Task {await store.swipe(product,action:"save")}};Spacer();Button("Dismiss",systemImage:"xmark") {Task {await store.swipe(product,action:"dislike"); if store.error == nil {dismiss()}}}}.font(.caption).disabled(store.busy)
                        }
                        if !complements.isEmpty {Divider();Text("Complete the look.").font(.system(size:29,design:.serif));ForEach(complements) {ProductRow(product:$0.product)}}
                        Text("Reference imagery is supplied from H&M in the design brief. No affiliation, live price or stock is claimed. Live shopping and actual virtual try-on require configured providers.").font(.caption).foregroundStyle(.secondary)
                    }.padding(.horizontal,24).padding(.bottom,35)
                }
            }.background(Theme.paper).navigationTitle("THE PERSONAL EDIT").navigationBarTitleDisplayMode(.inline).toolbar {ToolbarItem(placement:.topBarTrailing) {Button("Done") {dismiss()}}}
            .sheet(isPresented:$tryOn) {TryOnView(selectedProduct:product)}
            .sheet(isPresented:$assistant) {StylistView()}
            .task {if product.source?.contains("wardrobe") != true,let result:OutfitResult=try? await store.api.request("/outfits/complete",method:"POST",body:["product_id":product.id]) {complements=result.items}}
        }
    }
}

struct AvatarArt:UIViewRepresentable {
    let svg:String
    func makeUIView(context:Context)->WKWebView {let view=WKWebView();view.isOpaque=false;view.backgroundColor = .clear;view.scrollView.isScrollEnabled=false;return view}
    func updateUIView(_ view:WKWebView,context:Context) {view.loadHTMLString("<html><head><meta name='viewport' content='width=device-width,initial-scale=1'><style>body{margin:0;background:#eeece5;display:flex;justify-content:center;height:100vh}svg{height:100%;width:auto}</style></head><body>"+svg+"</body></html>",baseURL:nil)}
}
struct StyleAvatarView:View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @State private var avatar:Avatar?
    @State private var working=false
    var body:some View {NavigationStack {ScrollView {VStack(alignment:.leading,spacing:24) {
        Text("Your virtual muse.").font(.system(size:38,design:.serif))
        Text("An illustrated expression of your clothing preferences. Not a personal likeness, generated photograph, or fit simulation.").font(.subheadline).foregroundStyle(.secondary)
        if let avatar {AvatarArt(svg:avatar.svg).frame(height:420);Text(avatar.explanation).font(.subheadline);Text(avatar.notice).font(.caption).foregroundStyle(.secondary)}
        Button(working ? "Designing your style study…" : "Generate my AI style avatar",systemImage:"sparkles") {Task {working=true;defer{working=false};do {avatar=try await store.api.request("/stylist/avatar",method:"POST",body:[:])}catch {store.error=error.localizedDescription}}}.buttonStyle(.borderedProminent).disabled(working)
    }.padding(24)}.background(Theme.paper).navigationTitle("THE STYLE STUDY").navigationBarTitleDisplayMode(.inline).toolbar {Button("Done") {dismiss()}}}}
}
