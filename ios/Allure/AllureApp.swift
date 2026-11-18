import SwiftUI

@main
struct AllureApp: App {
    @State private var store = AppStore()
    var body: some Scene { WindowGroup { RootView().environment(store).tint(Theme.olive).preferredColorScheme(.light) } }
}

enum Theme {
    static let paper=Color(red:0.97,green:0.95,blue:0.92)
    static let ink=Color(red:0.18,green:0.21,blue:0.17)
    static let olive=Color(red:0.29,green:0.35,blue:0.22)
    static let sand=Color(red:0.88,green:0.83,blue:0.74)
}

struct RootView: View {
    @Environment(AppStore.self) private var store
    var body: some View {
        @Bindable var store=store
        Group {
            if store.authenticated {
                TabView {
                    Tab("Today",systemImage:"sun.horizon") { TodayView() }
                    Tab("Discover",systemImage:"rectangle.stack") { DiscoverView() }
                    Tab("Wardrobe",systemImage:"cabinet") { WardrobeView() }
                    Tab("Stylist",systemImage:"sparkles") { StylistView() }
                    Tab("You",systemImage:"person.crop.circle") { ProfileView() }
                }.task { await store.perform { try await store.refresh() } }
            } else { WelcomeView() }
        }
        .task {
            #if DEBUG
            if ProcessInfo.processInfo.arguments.contains("--allure-demo") && !store.authenticated {
                await store.connect(name:"Saksham",endpoint:store.endpoint)
                if store.authenticated {
                    await store.savePreferences(aesthetic:"minimalist",colors:"beige, olive",fit:"relaxed")
                    await store.setLocation(latitude:28.46,longitude:77.03,label:"Gurugram · demo city")
                }
            }
            #endif
        }
        .alert("A little heads-up",isPresented:Binding(get:{store.error != nil},set:{if !$0 {store.error=nil}})) { Button("OK") {store.error=nil} } message: { Text(store.error ?? "") }
    }
}

struct WelcomeView: View {
    @Environment(AppStore.self) private var store
    @State private var name=""
    @State private var endpoint="http://127.0.0.1:8766"
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment:.leading,spacing:28) {
                    Text("ALLURÉ").font(.system(size:48,weight:.regular,design:.serif)).tracking(6)
                    ZStack {
                        RoundedRectangle(cornerRadius:100).fill(Theme.sand.opacity(0.5)).frame(height:220)
                        Image(systemName:"tshirt").font(.system(size:110,weight:.ultraLight)).foregroundStyle(Theme.olive).rotationEffect(.degrees(-12))
                        Text("INDIVIDUALLY YOU").font(.caption.monospaced()).tracking(4).offset(y:85)
                    }
                    Text("Find your\nkind of style.").font(.system(size:44,weight:.regular,design:.serif)).lineSpacing(-3)
                    Text("A stylist that learns your taste, dresses for your day, and helps you make more of what you own.").foregroundStyle(.secondary)
                    VStack(alignment:.leading) { Text("What should we call you?").font(.caption); TextField("Your name",text:$name).textContentType(.givenName).padding().background(.white,in:RoundedRectangle(cornerRadius:14)) }
                    Button { Task {await store.connect(name:name,endpoint:endpoint)} } label: { HStack { Text(store.busy ? "Connecting…" : "Meet your stylist"); Spacer(); Image(systemName:"arrow.right") }.padding().frame(maxWidth:.infinity) }.buttonStyle(.borderedProminent).disabled(name.trimmingCharacters(in:.whitespaces).isEmpty || store.busy)
                    DisclosureGroup("Prototype connection") {
                        TextField("Backend URL",text:$endpoint).textInputAutocapitalization(.never).autocorrectionDisabled().keyboardType(.URL)
                        Text("Simulator: use 127.0.0.1. On iPhone, use your Mac’s local network address. Photos leave your device only when you choose an upload feature.").font(.caption).foregroundStyle(.secondary)
                    }.font(.caption)
                }.padding(28)
            }.background(Theme.paper).foregroundStyle(Theme.ink)
        }.onAppear {endpoint=store.endpoint}
    }
}

struct SectionHeading: View {
    let eyebrow: String; let title: String
    var body: some View { VStack(alignment:.leading,spacing:8) { Text(eyebrow.uppercased()).font(.caption.monospaced()).tracking(2).foregroundStyle(.secondary); Text(title).font(.system(size:34,design:.serif)) } }
}

struct ProductArtwork: View {
    let product: Product
    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius:24).fill(Theme.sand.opacity(0.45))
            if let url=product.imageUrl,let imageURL=URL(string:url) {
                AsyncImage(url:imageURL) { phase in if let image=phase.image {image.resizable().scaledToFit().padding()} else {Image(systemName:product.symbol).font(.system(size:74,weight:.ultraLight)).foregroundStyle(Theme.olive)} }
            } else {
                VStack(spacing:20) { Image(systemName:product.symbol).font(.system(size:90,weight:.ultraLight)); Text((product.colors ?? []).joined(separator:" / ").uppercased()).font(.caption.monospaced()).tracking(3) }.foregroundStyle(Theme.olive)
            }
        }.frame(height:230).accessibilityLabel(product.title)
    }
}

struct ProductRow: View {
    let product: Product
    var body: some View {
        HStack(spacing:14) {
            Image(systemName:product.symbol).font(.title2).frame(width:48,height:60).background(Theme.sand.opacity(0.4),in:RoundedRectangle(cornerRadius:12))
            VStack(alignment:.leading,spacing:4) { Text(product.title).font(.subheadline.weight(.medium)); Text(product.priceText).font(.caption).foregroundStyle(.secondary) }
            Spacer()
            if product.isDemo == true { Text("CONCEPT").font(.system(size:9,weight:.semibold)).padding(5).background(Theme.sand,in:Capsule()) }
        }.padding(.vertical,6)
    }
}
