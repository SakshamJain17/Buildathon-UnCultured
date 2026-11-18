import SwiftUI

@main
struct AllureApp: App {
    @State private var store = AppStore()
    var body: some Scene { WindowGroup { RootView().environment(store).tint(Theme.olive).preferredColorScheme(.light) } }
}

enum Theme {
    static let paper=Color.white
    static let ink=Color.black
    static let olive=Color(red:0.12,green:0.13,blue:0.11)
    static let sand=Color(white:0.92)
}

struct BrandSymbol:UIViewRepresentable {
    func makeUIView(context:Context)->UIView {
        let view=UIView();view.clipsToBounds=true
        if let path=Bundle.main.path(forResource:"allure-logo",ofType:"png"),let image=UIImage(contentsOfFile:path) {
            view.layer.contents=image.cgImage;view.layer.contentsGravity = .resize
            view.layer.contentsRect=CGRect(x:190.0/597.0,y:150.0/610.0,width:240.0/597.0,height:240.0/610.0)
        }
        view.backgroundColor=UIColor(red:0.969,green:0.961,blue:0.941,alpha:1);view.layer.cornerRadius=6
        return view
    }
    func updateUIView(_ uiView:UIView,context:Context) {}
}

struct BrandLockup:View {
    var size:CGFloat=32
    var body:some View {HStack(spacing:10) {
        BrandSymbol().frame(width:size,height:size).accessibilityHidden(true)
        Text("ALLURÉ").font(.system(size:size*0.58,design:.serif)).tracking(3)
    }.accessibilityElement(children:.ignore).accessibilityLabel("ALLURÉ")}
}

struct RootView: View {
    @Environment(AppStore.self) private var store
    @State private var launching=true
    var body: some View {
        @Bindable var store=store
        ZStack {
            Group {
                if store.authenticated {
                    TabView(selection:$store.selectedTab) {
                        Tab("Discover",systemImage:"rectangle.stack",value:AppTab.discover) {DiscoverView()}
                        Tab("Wardrobe",systemImage:"cabinet",value:AppTab.wardrobe) {WardrobeView()}
                        Tab("Saved",systemImage:"bookmark",value:AppTab.saved) {SavedView()}
                        Tab("You",systemImage:"person.crop.circle",value:AppTab.profile) {ProfileView()}
                    }
                    .tabViewBottomAccessory {
                        Button {store.showAssistant=true} label: {
                            HStack(spacing:13) {Circle().fill(.white.opacity(0.8)).frame(width:18,height:18).blur(radius:2);Text("Ask Allure to do it…").font(.system(size:13));Spacer();Image(systemName:"arrow.up.right").font(.caption)}.foregroundStyle(.white).padding(.horizontal,20).padding(.vertical,14).background(.black,in:Capsule()).padding(.horizontal,16).padding(.vertical,6)
                        }.buttonStyle(.plain)
                    }
                } else {WelcomeView()}
            }
            if launching {MonochromeSplash().transition(.opacity)}
        }
        .sheet(isPresented:$store.showAssistant) {StylistView()}
        .sheet(isPresented:$store.showWalkthrough) {WalkthroughView()}
        .task {
            if store.authenticated {await store.perform {try await store.refresh()}}
            #if DEBUG
            if ProcessInfo.processInfo.arguments.contains("--allure-ready") && !store.authenticated {await store.connect(name:"Style explorer",endpoint:store.endpoint)}
            if (ProcessInfo.processInfo.arguments.contains("--allure-sample") || ProcessInfo.processInfo.arguments.contains("--allure-ready")) && store.authenticated {await store.loadSample();store.showWalkthrough=false}
            #endif
            try? await Task.sleep(for:.milliseconds(850))
            withAnimation(.easeOut(duration:0.4)) {launching=false}
        }
        .alert("A little heads-up",isPresented:Binding(get:{store.error != nil},set:{if !$0 {store.error=nil}})) {Button("OK") {store.error=nil}} message:{Text(store.error ?? "")}
    }
}

struct OrbCluster:View {
    @Environment(\.accessibilityReduceMotion) private var reduced
    @State private var moving=false
    var body:some View {
        GeometryReader {geo in
            ZStack {
                Circle().fill(Color.gray.opacity(0.22)).frame(width:geo.size.width*0.48).blur(radius:20).offset(x:moving ? -35:25,y:moving ? 30:-20)
                Circle().fill(Color.gray.opacity(0.15)).frame(width:geo.size.width*0.6).blur(radius:25).offset(x:moving ? 40:-25,y:moving ? -35:25)
                Circle().fill(Color.black.opacity(0.09)).frame(width:geo.size.width*0.35).blur(radius:20).offset(x:moving ? -10:45,y:moving ? -45:15)
            }.frame(width:geo.size.width,height:geo.size.height)
        }.onAppear {if !reduced {withAnimation(.easeInOut(duration:3.5).repeatForever(autoreverses:true)){moving=true}}}
    }
}
struct MonochromeSplash:View {
    var body:some View {ZStack {Color.white.ignoresSafeArea();OrbCluster().frame(width:330,height:330);VStack(spacing:24) {BrandSymbol().frame(width:140,height:140).accessibilityLabel("ALLURÉ. Your fashion, your way.");Text("YOUR STYLE, COMING INTO FOCUS.").font(.system(size:8)).tracking(2).foregroundStyle(.secondary)}}}
}
struct WelcomeView:View {
    @Environment(AppStore.self) private var store
    @State private var name=""
    @State private var endpoint="http://127.0.0.1:8766"
    var body:some View {NavigationStack {ScrollView {VStack(alignment:.leading,spacing:26) {
        BrandLockup(size:48).padding(.top,20)
        ZStack {OrbCluster().frame(height:200);Text("Individually you.").font(.system(size:28,design:.serif))}
        Text("Your personal stylist.\nA little more you.").font(.system(size:38,design:.serif))
        Text("Swipe what you love. Build from your wardrobe. Ask Allure to take care of the details.").font(.subheadline).foregroundStyle(.secondary)
        TextField("Your name",text:$name).textContentType(.givenName).padding().background(Color(white:0.96),in:RoundedRectangle(cornerRadius:12))
        Button {Task {await store.connect(name:name,endpoint:endpoint)}} label:{HStack {Text(store.busy ? "Getting your edit ready…" : "Meet your stylist");Spacer();Image(systemName:"arrow.up.right")}.padding(12).frame(maxWidth:.infinity)}.buttonStyle(.borderedProminent).disabled(name.trimmingCharacters(in:.whitespaces).isEmpty || store.busy)
        Button("Try the sample walkthrough") {Task {await store.connect(name:"Style explorer",endpoint:endpoint);if store.authenticated {await store.loadSample()}}}.font(.subheadline).frame(maxWidth:.infinity).disabled(store.busy)
        DisclosureGroup("Prototype connection") {TextField("Backend URL",text:$endpoint).keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled();Text("Simulator: 127.0.0.1. On an iPhone use the public HTTPS demo URL. Provider keys stay on the backend.").font(.caption).foregroundStyle(.secondary)}.font(.caption)
    }.padding(28)}.background(.white)}.onAppear {endpoint=store.endpoint}}
}

struct WalkthroughView:View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @State private var page=0
    private let titles=["One card. Three choices.","A wardrobe with possibilities.","One bot. Actual actions.","See your style evolve."]
    private let descriptions=["Right to like. Left to dismiss. Down to save. Buttons work too. Dismissed identities stay out of new recommendations for your profile.","Sample pieces are labelled. Add your own photograph, let vision suggest labels, and review them before saving.","Ask Allure to save this piece, change your preferred colours, build an outfit, or open a feature. Actions appear in the tool trace.","Your passport tracks likes, saves, dismissals and wardrobe pieces. Photos and generation still require your inputs and consent."]
    private let symbols=["rectangle.stack","cabinet","sparkles","chart.bar"]
    var body:some View {NavigationStack {VStack(spacing:30) {
        Spacer();ZStack {OrbCluster().frame(width:230,height:180);Image(systemName:symbols[page]).font(.system(size:65,weight:.ultraLight))};Text(titles[page]).font(.system(size:32,design:.serif)).multilineTextAlignment(.center);Text(descriptions[page]).font(.subheadline).foregroundStyle(.secondary).multilineTextAlignment(.center).lineSpacing(5)
        HStack(spacing:8) {ForEach(0..<4,id:\.self) {i in Capsule().fill(i==page ? Color.black:Color.gray.opacity(0.2)).frame(width:20,height:4)}}
        Spacer();Button(page==3 ? "Start exploring" : "Next") {if page==3 {store.selectedTab = .discover;dismiss()} else {withAnimation {page+=1}}}.buttonStyle(.borderedProminent).controlSize(.large).frame(maxWidth:.infinity)
        Text("Sample data is illustrative. No prices, purchases or personal-photo results are fabricated.").font(.caption2).foregroundStyle(.secondary).multilineTextAlignment(.center)
    }.padding(30).toolbar {Button("Skip") {dismiss()}}}}
}
struct SavedView:View {
    @Environment(AppStore.self) private var store
    var body:some View {NavigationStack {ScrollView {VStack(alignment:.leading,spacing:20) {Text("Your saved edit.").font(.system(size:34,design:.serif));if store.saved.isEmpty {ContentUnavailableView("A place for possibilities",systemImage:"bookmark",description:Text("Swipe down or tap Save to collect the pieces you want to return to."))};ForEach(store.saved){ProductRow(product:$0)}}.padding(24)}.background(.white).navigationTitle("").toolbar {ToolbarItem(placement:.principal) {BrandLockup(size:26)}}.navigationBarTitleDisplayMode(.inline)}}
}

struct SectionHeading: View {
    let eyebrow: String; let title: String
    var body: some View { VStack(alignment:.leading,spacing:8) { Text(eyebrow.uppercased()).font(.caption.monospaced()).tracking(2).foregroundStyle(.secondary); Text(title).font(.system(size:34,design:.serif)) } }
}

struct ProductArtwork: View {
    @Environment(AppStore.self) private var store
    let product: Product
    var height: CGFloat = 360
    var showWholePhoto: Bool = false
    @State private var privatePhoto: UIImage?
    var body: some View {
        ZStack {
            Theme.sand.opacity(0.35)
            if product.source?.contains("wardrobe") == true {
                if let privatePhoto { Image(uiImage:privatePhoto).resizable().scaledToFit() }
                else { ProgressView() }
            } else if let source=product.imageUrl,let url=URL(string:source,relativeTo:URL(string:store.endpoint)) {
                AsyncImage(url:url) { phase in
                    if let image=phase.image { image.resizable().aspectRatio(contentMode:showWholePhoto ? .fit : .fill) }
                    else { VStack { ProgressView(); Text("Your style reference").font(.caption).padding() } }
                }
            } else {
                VStack(spacing:20) { Image(systemName:product.symbol).font(.system(size:70,weight:.ultraLight)); Text("STYLE CONCEPT").font(.caption.monospaced()).tracking(3) }.foregroundStyle(Theme.olive)
            }
        }.frame(maxWidth:.infinity).frame(height:height).clipped().accessibilityLabel(product.title)
        .task(id:product.id) { if product.source?.contains("wardrobe") == true,let data=try? await store.api.image(product.id) {privatePhoto=UIImage(data:data)} }
    }
}

struct ProductRow: View {
    let product: Product
    @State private var selected=false
    var body: some View {
        Button {selected=true} label: {
            HStack(spacing:16) {
                ProductArtwork(product:product,height:100).frame(width:75)
                VStack(alignment:.leading,spacing:8) {
                    Text(product.title).font(.system(size:19,design:.serif)).foregroundStyle(Theme.ink)
                    Text(product.priceText).font(.system(size:9)).tracking(0.6).foregroundStyle(.secondary)
                }
                Spacer(minLength:0)
                Image(systemName:"arrow.up.right").font(.caption).foregroundStyle(Theme.ink)
            }.padding(.vertical,8)
        }.buttonStyle(.plain).sheet(isPresented:$selected) {ProductDetailView(product:product)}
    }
}
