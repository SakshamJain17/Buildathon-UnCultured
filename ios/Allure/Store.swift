import SwiftUI
import CoreLocation
import Observation

@MainActor @Observable
final class AppStore {
    let api: API
    var name = ""
    var selectedTab:AppTab = .discover
    var showAssistant=false
    var assistantDraft=""
    var assistantAutoSend=false
    var showWalkthrough=false
    var profileTarget:String?
    var focusedProductID:String?
    var insights:Insights?
    var authenticated = false
    var error: String?
    var busy = false
    var feed: [Ranked] = []
    var daily: Daily?
    var wardrobe: [Product] = []
    var saved: [Product] = []
    var preferences: Preferences?
    var inspirations: [Inspiration] = []
    var location: [String: Any]?
    var locationLabel = "Choose your city"
    var endpoint: String { api.baseURL }
    init() {
        #if targetEnvironment(simulator)
        let defaultEndpoint="http://127.0.0.1:8766"
        #else
        let defaultEndpoint="https://allure-sakshamjain17s-projects.vercel.app"
        #endif
        api = API(baseURL: UserDefaults.standard.string(forKey:"allure-backend") ?? defaultEndpoint)
        api.token = Vault.load(account:api.baseURL)
        authenticated = !api.token.isEmpty
        name = UserDefaults.standard.string(forKey:"allure-name") ?? ""
    }
    func connect(name: String, endpoint: String) async {
        await perform {
            self.api.baseURL = endpoint.trimmingCharacters(in:.whitespacesAndNewlines).trimmingCharacters(in:CharacterSet(charactersIn:"/"))
            let session: Session = try await self.api.request("/sessions",method:"POST",body:["name":name])
            self.api.token = session.token; self.name = session.name; self.authenticated = true
            Vault.save(session.token,account:self.api.baseURL)
            UserDefaults.standard.set(self.api.baseURL,forKey:"allure-backend"); UserDefaults.standard.set(session.name,forKey:"allure-name")
            try await self.refresh()
        }
    }
    func refresh() async throws {
        let me: Profile = try await api.request("/me"); name=me.name; preferences=me.preferences; inspirations=me.preferences.inspirations ?? []
        let result: Feed = try await api.request("/recommendations?limit=50"); feed=result.items
        let closet: WardrobeList = try await api.request("/wardrobe"); wardrobe=closet.items
        let savedItems: ProductList = try await api.request("/saved"); saved=savedItems.products
        insights=try await api.request("/me/insights")
    }
    func perform(_ operation: () async throws -> Void) async {
        guard !busy else { return }; busy=true; defer { busy=false }
        do { try await operation() } catch { self.error=error.localizedDescription }
    }
    func swipe(_ item: Product, action: String) async {
        await perform {
            let _: EmptyResult = try await self.api.request("/swipes",method:"POST",body:["product_id":item.id,"action":action],idempotency:UUID().uuidString)
            self.feed.removeAll { $0.id==item.id }
            if action == "dislike" { self.daily=nil }
            try await self.refresh()
        }
    }
    func setLocation(latitude: Double, longitude: Double, label: String) async {
        let coords: [String: Any] = ["latitude":(latitude*100).rounded()/100,"longitude":(longitude*100).rounded()/100]
        location=coords; locationLabel=label
        await perform { self.daily = try await self.api.request("/stylist/daily",method:"POST",body:["location":coords]) }
    }
    func savePreferences(aesthetic: String, colors: String, fit: String) async {
        await perform {
            let _: EmptyResult = try await self.api.request("/me/preferences",method:"PUT",body:["aesthetics":[aesthetic],"preferred_colors":colors.split(separator:",").map{ $0.trimmingCharacters(in:.whitespaces).lowercased() },"silhouettes":[fit]])
            try await self.refresh(); self.daily=nil
        }
    }
    func follow(_ name: String, tags: String) async {
        let entry=Inspiration(name:name,tags:tags.split(separator:",").map{$0.trimmingCharacters(in:.whitespaces).lowercased()}.filter{!$0.isEmpty})
        await updateInspirations(inspirations.filter{$0.name.caseInsensitiveCompare(name) != .orderedSame}+[entry])
    }
    func updateInspirations(_ items: [Inspiration]) async {
        await perform {
            let _: EmptyResult = try await self.api.request("/me/inspirations",method:"PUT",body:["inspirations":items.map{["name":$0.name,"tags":$0.tags] as [String: Any]}])
            try await self.refresh(); self.daily=nil
        }
    }
    func loadSample() async {
        await perform {let _:EmptyResult=try await self.api.request("/demo/seed",method:"POST",body:[:]);try await self.refresh();self.showWalkthrough=true}
    }
    func applyBotActions(_ actions:[UIAction]) async throws {
        if actions.contains(where:{$0.type == "refresh"}) {daily=nil;try await refresh()}
        for action in actions where action.type == "open_feature" {
            switch action.feature {
            case "discover":selectedTab = .discover;showAssistant=false
            case "wardrobe":selectedTab = .wardrobe;showAssistant=false
            case "saved":selectedTab = .saved;showAssistant=false
            case "profile":selectedTab = .profile;showAssistant=false
            case "analyze_style","palette","hair":selectedTab = .profile;profileTarget=action.feature;showAssistant=false
            default:break
            }
        }
    }
    func signOut() { Vault.save("",account:api.baseURL); api.token=""; authenticated=false; feed=[]; daily=nil; wardrobe=[]; saved=[]; location=nil; locationLabel="Choose your city"; preferences=nil; inspirations=[] }
}

@MainActor @Observable
final class LocationAccess: NSObject, @preconcurrency CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    var coordinate: CLLocationCoordinate2D?
    var message: String?
    var locating=false
    override init() { super.init(); manager.delegate=self; manager.desiredAccuracy=kCLLocationAccuracyKilometer }
    func request() {
        message=nil; locating=true
        switch manager.authorizationStatus {
        case .notDetermined: manager.requestWhenInUseAuthorization()
        case .authorizedAlways,.authorizedWhenInUse: manager.requestLocation()
        default: locating=false; message="Location is off. Choose a city instead, or enable location in Settings."
        }
    }
    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        if locating && (manager.authorizationStatus == .authorizedWhenInUse || manager.authorizationStatus == .authorizedAlways) { manager.requestLocation() }
        else if manager.authorizationStatus == .denied || manager.authorizationStatus == .restricted { locating=false; message="Choose a city to get weather without location access." }
    }
    func locationManager(_ manager: CLLocationManager,didUpdateLocations locations:[CLLocation]) { coordinate=locations.last?.coordinate; locating=false }
    func locationManager(_ manager: CLLocationManager,didFailWithError error:Error) { locating=false; message="Could not locate you. Choose a city instead." }
}
