import SwiftUI

struct TodayView: View {
    @Environment(AppStore.self) private var store
    @State private var location = LocationAccess()
    @State private var showCities=false
    @State private var showTryOn=false
    @State private var featured:Product?
    @State private var showAvatar=false
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment:.leading,spacing:26) {
                    HStack { Text("ALLURÉ").font(.system(size:24,design:.serif)).tracking(4); Spacer(); Text("YOUR DAILY EDIT").font(.system(size:9,design:.monospaced)).tracking(2) }
                    SectionHeading(eyebrow:"Made for your day",title:"Hey \(store.name).\nLet’s make it you.")
                    if let product=store.daily?.outfit.first(where:{$0.product.imageUrl != nil})?.product ?? store.feed.first(where:{$0.product.imageUrl != nil})?.product {
                        Button {featured=product} label: {
                            ZStack(alignment:.bottomLeading) {
                                ProductArtwork(product:product,height:430)
                                LinearGradient(colors:[.clear,.black.opacity(0.65)],startPoint:.center,endPoint:.bottom)
                                VStack(alignment:.leading,spacing:12) {
                                    Text("THE PERSONAL COLLECTION").font(.system(size:9)).tracking(2)
                                    Text("A new point\nof view.").font(.system(size:42,design:.serif))
                                    Text("EXPLORE YOUR EDIT ↗").font(.system(size:9)).tracking(1.5)
                                }.foregroundStyle(.white).padding(24)
                            }.frame(height:430)
                        }.buttonStyle(.plain)
                    }
                    HStack { Image(systemName:"location"); Text(store.locationLabel).font(.subheadline); Spacer(); Button("Change") {showCities=true}.font(.caption) }
                    if let daily=store.daily {
                        VStack(alignment:.leading,spacing:14) {
                            HStack { Image(systemName:daily.weather.tags.contains("rain") ? "cloud.rain" : "cloud.sun").font(.largeTitle); Spacer(); Text("\(Int(daily.weather.current.apparentTemperature ?? 0))°").font(.system(size:48,design:.serif)) }
                            Text(daily.greeting).font(.body).lineSpacing(4)
                            Text("\(daily.weather.source) · \(Int(daily.weather.precipitationProbabilityPercent ?? 0))% daily precipitation chance").font(.caption).foregroundStyle(.secondary)
                        }.padding(22).background(.white,in:RoundedRectangle(cornerRadius:24))
                        Text("THE OUTFIT DIRECTION").font(.caption.monospaced()).tracking(2)
                        ForEach(daily.outfit) { item in VStack(alignment:.leading) { ProductRow(product:item.product); Text(item.reasons.joined(separator:" · ")).font(.caption).foregroundStyle(.secondary) } }
                        ForEach(daily.warnings,id:\.self) {Text($0).font(.caption).foregroundStyle(.secondary)}
                    } else {
                        VStack(alignment:.leading,spacing:16) {
                            Image(systemName:"sun.horizon").font(.system(size:40,weight:.light))
                            Text("Dress for your day.").font(.title2.weight(.medium))
                            Text("Share a one-time location or choose a city. We’ll use the actual forecast to suggest your next outfit.").foregroundStyle(.secondary)
                            Button(location.locating ? "Finding your location…" : "Use my location",systemImage:"location.fill") {location.request()}.buttonStyle(.borderedProminent).disabled(location.locating || store.busy)
                            Button("Choose a city instead") {showCities=true}
                            if let message=location.message {Text(message).font(.caption).foregroundStyle(.secondary)}
                        }.padding(24).frame(maxWidth:.infinity,alignment:.leading).background(.white,in:RoundedRectangle(cornerRadius:24))
                    }
                    Button {showTryOn=true} label: { HStack { Image(systemName:"viewfinder").font(.title2); VStack(alignment:.leading) {Text("The fitting room").font(.headline); Text("Preview a garment on you").font(.caption)}; Spacer(); Image(systemName:"arrow.up.right") }.padding(22).foregroundStyle(.white).background(Theme.olive,in:RoundedRectangle(cornerRadius:22)) }
                    Button {showAvatar=true} label: {HStack {VStack(alignment:.leading,spacing:8) {Text("YOUR VIRTUAL MUSE").font(.system(size:9)).tracking(2);Text("An illustrated point of view.").font(.system(size:26,design:.serif))};Spacer();Image(systemName:"arrow.up.right")}.padding(22).foregroundStyle(Theme.ink).background(.white)}.buttonStyle(.plain)
                    Text("FIND YOUR KIND OF STYLE.").font(.caption.monospaced()).tracking(3).foregroundStyle(.secondary).padding(.vertical)
                }.padding(24)
            }.background(Theme.paper).toolbar(.hidden,for:.navigationBar)
            .sheet(isPresented:$showCities) {CityPicker()}
            .sheet(isPresented:$showTryOn) {TryOnView()}
            .sheet(item:$featured) {ProductDetailView(product:$0)}
            .sheet(isPresented:$showAvatar) {StyleAvatarView()}
            .onChange(of:location.coordinate?.latitude) { _,_ in
                if let coordinate=location.coordinate {Task {await store.setLocation(latitude:coordinate.latitude,longitude:coordinate.longitude,label:"Near you")}}
            }
        }
    }
}

struct CityPicker: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @State private var query=""
    @State private var cities: [City]=[]
    @State private var searching=false
    var body: some View {
        NavigationStack {
            List {
                Section { HStack { TextField("Search your city",text:$query).onSubmit {Task {await search()}}; Button("Search") {Task {await search()}}.disabled(query.count<2 || searching) } }
                ForEach(cities) { city in Button {Task {await store.setLocation(latitude:city.latitude,longitude:city.longitude,label:city.name); dismiss()}} label: {VStack(alignment:.leading) {Text(city.name); Text([city.region,city.country].compactMap{$0}.joined(separator:", ")).font(.caption).foregroundStyle(.secondary)}} }
                if searching {ProgressView()}
                Section {Text("Coordinates are rounded and used for weather. Your city is not saved to your profile.").font(.caption).foregroundStyle(.secondary)}
            }.navigationTitle("Your weather, your city").navigationBarTitleDisplayMode(.inline).toolbar {ToolbarItem(placement:.cancellationAction) {Button("Done") {dismiss()}}}
        }
    }
    func search() async {
        searching=true; defer {searching=false}
        do { let value=query.addingPercentEncoding(withAllowedCharacters:.urlQueryAllowed) ?? query; cities=try await store.api.request("/locations/search?q=\(value)") } catch {store.error=error.localizedDescription}
    }
}

struct DiscoverView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var drag: CGSize = .zero
    @State private var sendingSwipe=false
    @State private var modelLooks=true
    private let modelIDs:Set<String> = ["ref_f8ed3becb467d2f3","ref_db22deae6cda0525","ref_9d4b3874f67fbd53","ref_eb0b325eb2666025"]
    private var discoveryFeed:[Ranked] {modelLooks ? store.feed.filter {modelIDs.contains($0.id)} : store.feed}
    @State private var swipeLabel=""
    @State private var showSaved=false
    @State private var query=""
    @State private var selected:Product?
    @State private var today=false
    @State private var results: [Product]=[]
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment:.leading,spacing:22) {
                    HStack {Text("Your next favourite.").font(.system(size:31,design:.serif));Spacer();Button {today=true} label:{Image(systemName:"cloud.sun")}.accessibilityLabel("Weather and your daily outfit")}
                    Picker("Explore",selection:$modelLooks) {Text("Styled looks").tag(true);Text("Individual pieces").tag(false)}.pickerStyle(.segmented)
                    if let item=discoveryFeed.first {
                        discoveryCard(item.product)
                        HStack(spacing:28) {
                            actionButton("Dismiss",symbol:"xmark",action:"dislike",product:item.product)
                            actionButton("Save",symbol:"bookmark",action:"save",product:item.product)
                            actionButton("Like",symbol:"heart",action:"like",product:item.product)
                        }.frame(maxWidth:.infinity)
                        Text("← Dismiss · ↓ Save · Like →").font(.caption).foregroundStyle(.secondary).frame(maxWidth:.infinity)
                    } else {
                        ContentUnavailableView("You’re all caught up",systemImage:"checkmark.seal",description:Text("Your dismissed items stay hidden. Switch to Individual pieces to explore more of your edit, or ask Allure to find something new."))
                    }
                    DisclosureGroup("Find something specific") {
                        HStack {TextField("e.g. olive rain jacket",text:$query).textFieldStyle(.roundedBorder);Button("Search") {Task {await liveSearch()}}.disabled(query.count<2 || store.busy)}
                    }.font(.caption)
                    ForEach(results) {p in VStack(alignment:.leading) {ProductRow(product:p); if let url=p.merchantUrl,let link=URL(string:url) {Link("View listing",destination:link).font(.caption)}; Button("Dismiss this item") {Task {await store.swipe(p,action:"dislike"); if store.error == nil {results.removeAll{$0.id==p.id}}}}.font(.caption)} }
                }.padding(24)
                .offset(x:reduceMotion ? 0 : drag.width,y:reduceMotion ? 0 : drag.height)
            }.background(Theme.paper).navigationTitle("ALLURÉ").navigationBarTitleDisplayMode(.inline)
            .sheet(isPresented:$showSaved) {NavigationStack {List(store.saved) {ProductRow(product:$0)}.navigationTitle("Saved for later").toolbar {Button("Done") {showSaved=false}}}}
            .sheet(item:$selected) {ProductDetailView(product:$0)}
            .sheet(isPresented:$today) {TodayView()}
            .onChange(of:discoveryFeed.first?.id,initial:true) {_,id in store.focusedProductID=id}
            .refreshable {await store.perform {try await store.refresh()}}
        }
    }
    func discoveryCard(_ product:Product) -> some View {
        VStack(alignment:.leading,spacing:10) {
            ProductArtwork(product:product,height:380,showWholePhoto:true)
            if modelLooks {Text("THE LOOK / ON MODEL").font(.caption2).tracking(2).foregroundStyle(.secondary)}
            Text(product.title).font(.system(size:24,design:.serif))
            Text(product.priceText).font(.caption).foregroundStyle(.secondary)
        }.padding(12).background(.white,in:RoundedRectangle(cornerRadius:18))
        .overlay {RoundedRectangle(cornerRadius:18).stroke(Color.gray.opacity(0.15))}
        .overlay(alignment:.top) {
            if !swipeLabel.isEmpty {Text(swipeLabel).font(.headline).tracking(2).padding(12).background(.white,in:RoundedRectangle(cornerRadius:8)).overlay {RoundedRectangle(cornerRadius:8).stroke(.black,lineWidth:2)}.padding(.top,24)}
        }
        .shadow(color:.black.opacity(0.06),radius:18,y:8)

        .onTapGesture {if !sendingSwipe {selected=product}}
        .highPriorityGesture(DragGesture(minimumDistance:12).onChanged { value in
            guard !sendingSwipe && !store.busy else {return}
            drag=value.translation
            swipeLabel=drag.height > abs(drag.width)*1.15 ? "SAVE FOR LATER" : drag.width > 0 ? "MY STYLE" : "PASS"
        }.onEnded { value in
            guard !sendingSwipe && !store.busy else {return}
            let x=value.translation.width,y=value.translation.height
            let action=y>70 && y>abs(x)*1.15 ? "save" : abs(x)>70 && abs(x)>abs(y)*0.8 ? (x>0 ? "like" : "dislike") : nil
            if let action {commitSwipe(product,action:action)} else {withAnimation(reduceMotion ? nil : .spring(response:0.35,dampingFraction:0.75)) {drag = .zero;swipeLabel=""}}
        })
        .accessibilityElement(children:.combine)
        .accessibilityLabel(product.title+". "+product.priceText)
        .accessibilityAction(named:"Like") {commitSwipe(product,action:"like")}
        .accessibilityAction(named:"Save") {commitSwipe(product,action:"save")}
        .accessibilityAction(named:"Dismiss") {commitSwipe(product,action:"dislike")}
        .accessibilityAction(named:"View details") {selected=product}
    }
    func commitSwipe(_ product:Product,action:String) {
        guard !sendingSwipe && !store.busy else {return}
        sendingSwipe=true
        swipeLabel=action == "save" ? "SAVE FOR LATER" : action == "like" ? "MY STYLE" : "PASS"
        Task { @MainActor in
            withAnimation(reduceMotion ? nil : .easeIn(duration:0.25)) {
                drag=action == "save" ? CGSize(width:0,height:900) : CGSize(width:action == "like" ? 650 : -650,height:35)
            }
            if !reduceMotion {try? await Task.sleep(for:.milliseconds(250))}
            await store.swipe(product,action:action)
            var transaction=Transaction();transaction.disablesAnimations=true
            withTransaction(transaction) {drag = .zero;swipeLabel="";sendingSwipe=false}
        }
    }
    func actionButton(_ title:String,symbol:String,action:String,product:Product) -> some View {
        Button {commitSwipe(product,action:action)} label: {VStack(spacing:8) {Image(systemName:symbol).font(.title2).frame(width:52,height:52).background(.white,in:Circle()); Text(title).font(.caption)}}.disabled(store.busy || sendingSwipe).accessibilityLabel(title+" "+product.title)
    }
    func liveSearch() async {await store.perform {let value:ProductList=try await store.api.request("/products/search",method:"POST",body:["query":query]); results=value.products}}
}
