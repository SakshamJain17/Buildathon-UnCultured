import SwiftUI

struct TodayView: View {
    @Environment(AppStore.self) private var store
    @State private var location = LocationAccess()
    @State private var showCities=false
    @State private var showTryOn=false
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment:.leading,spacing:26) {
                    HStack { Text("ALLURÉ").font(.system(size:24,design:.serif)).tracking(4); Spacer(); Text("YOUR DAILY EDIT").font(.system(size:9,design:.monospaced)).tracking(2) }
                    SectionHeading(eyebrow:"Made for your day",title:"Hey \(store.name).\nLet’s make it you.")
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
                    Text("FIND YOUR KIND OF STYLE.").font(.caption.monospaced()).tracking(3).foregroundStyle(.secondary).padding(.vertical)
                }.padding(24)
            }.background(Theme.paper).toolbar(.hidden,for:.navigationBar)
            .sheet(isPresented:$showCities) {CityPicker()}
            .sheet(isPresented:$showTryOn) {TryOnView()}
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
    @State private var drag: CGFloat=0
    @State private var showSaved=false
    @State private var query=""
    @State private var results: [Product]=[]
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment:.leading,spacing:22) {
                    SectionHeading(eyebrow:"A little more you",title:"Your next favourite.")
                    Text("Right to like. Left to dismiss for this profile. You can also use the buttons below.").font(.subheadline).foregroundStyle(.secondary)
                    if let item=store.feed.first {
                        VStack(alignment:.leading,spacing:16) {
                            ProductArtwork(product:item.product)
                            HStack {Text(item.product.title).font(.system(size:27,design:.serif)); Spacer()}
                            Text(item.product.priceText).font(.caption).foregroundStyle(.secondary)
                            Text(item.reasons.joined(separator:" · ")).font(.subheadline).foregroundStyle(.secondary)
                            if item.product.isDemo == true {Label("Fictional catalogue example",systemImage:"info.circle").font(.caption)}
                        }.padding(20).background(.white,in:RoundedRectangle(cornerRadius:28))
                        .offset(x:reduceMotion ? 0 : drag).rotationEffect(.degrees(reduceMotion ? 0 : Double(drag/25)))
                        .gesture(DragGesture().onChanged {drag=$0.translation.width}.onEnded { value in
                            let action=value.translation.width < -80 ? "dislike" : value.translation.width > 80 ? "like" : nil
                            withAnimation(reduceMotion ? nil : .snappy) {drag=0}
                            if let action {Task {await store.swipe(item.product,action:action)}}
                        })
                        HStack(spacing:28) {
                            actionButton("Dismiss",symbol:"xmark",action:"dislike",product:item.product)
                            actionButton("Save",symbol:"bookmark",action:"save",product:item.product)
                            actionButton("Like",symbol:"heart",action:"like",product:item.product)
                        }.frame(maxWidth:.infinity)
                    } else {
                        ContentUnavailableView("You’re all caught up",systemImage:"checkmark.seal",description:Text("Your dismissed items stay hidden. Try live search for more options when the shopping provider is configured."))
                    }
                    Divider().padding(.vertical,10)
                    Text("Find something specific").font(.title3.weight(.medium))
                    HStack {TextField("e.g. olive rain jacket",text:$query).textFieldStyle(.roundedBorder); Button("Search") {Task {await liveSearch()}}.disabled(query.count<2 || store.busy)}
                    ForEach(results) {p in VStack(alignment:.leading) {ProductRow(product:p); if let url=p.merchantUrl,let link=URL(string:url) {Link("View listing",destination:link).font(.caption)}; Button("Dismiss this item") {Task {await store.swipe(p,action:"dislike"); if store.error == nil {results.removeAll{$0.id==p.id}}}}.font(.caption)} }
                }.padding(24)
            }.background(Theme.paper).navigationTitle("Discover").navigationBarTitleDisplayMode(.inline)
            .toolbar {ToolbarItem(placement:.topBarTrailing) {Button("Saved",systemImage:"bookmark") {showSaved=true}}}
            .sheet(isPresented:$showSaved) {NavigationStack {List(store.saved) {ProductRow(product:$0)}.navigationTitle("Saved for later").toolbar {Button("Done") {showSaved=false}}}}
            .refreshable {await store.perform {try await store.refresh()}}
        }
    }
    func actionButton(_ title:String,symbol:String,action:String,product:Product) -> some View {
        Button {Task {await store.swipe(product,action:action)}} label: {VStack(spacing:8) {Image(systemName:symbol).font(.title2).frame(width:60,height:60).background(.white,in:Circle()); Text(title).font(.caption)}}.disabled(store.busy).accessibilityLabel(title+" "+product.title)
    }
    func liveSearch() async {await store.perform {let value:ProductList=try await store.api.request("/products/search",method:"POST",body:["query":query]); results=value.products}}
}
