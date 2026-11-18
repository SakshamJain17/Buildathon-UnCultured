import Foundation

struct Envelope<T: Decodable>: Decodable { let success: Bool; let data: T?; let error: APIMessage? }
struct APIMessage: Decodable { let code: String; let message: String }
struct Session: Decodable { let userId: String; let name: String; let token: String }
struct Profile: Decodable { let name: String; let preferences: Preferences }
struct Preferences: Decodable { var aesthetics: [String]?; var preferredColors: [String]?; var silhouettes: [String]?; var inspirations: [Inspiration]?;var inferredProfile:[String:[String]]? }
struct Inspiration: Codable, Identifiable { var id: String { name }; let name: String; let tags: [String] }
struct Product: Decodable, Identifiable {
    let id: String; let title: String; let category: String?; let colors: [String]?; let aesthetics: [String]?
    let price: Double?; let currency: String?; let imageUrl: String?; let merchantUrl: String?; let isDemo: Bool?; let source: String?
    var symbol: String {
        switch category { case "bottoms": return "figure.walk"; case "footwear": return "shoe"; case "accessories": return "bag"; default: return "tshirt" }
    }
    var priceText: String { guard let price else { return source == "reference_catalogue" ? "REFERENCE EDIT · PRICE UNVERIFIED" : isDemo == true ? "STYLE CONCEPT · NOT FOR SALE" : "FROM YOUR WARDROBE" }; return "\(currency ?? "") \(Int(price))" }
}
struct Ranked: Decodable, Identifiable { var id: String { product.id }; let product: Product; let reasons: [String]; let score: Double }
struct Feed: Decodable { let items: [Ranked] }
struct ProductList: Decodable { let products: [Product] }
struct WardrobeList: Decodable { let items: [Product] }
struct WardrobeCreated: Decodable { let item: Product }
struct City: Decodable, Identifiable { var id: String { "\(name)-\(latitude)-\(longitude)" }; let name: String; let region: String?; let country: String?; let latitude: Double; let longitude: Double }
struct WeatherCurrent: Decodable { let apparentTemperature: Double?; let temperature2m: Double? }
struct Weather: Decodable { let current: WeatherCurrent; let source: String; let precipitationProbabilityPercent: Double?; let retrievedAt: String?; let tags: [String] }
struct Daily: Decodable { let greeting: String; let weather: Weather; let outfit: [Ranked]; let stylingNotes: [String]; let warnings: [String] }
struct Run: Decodable { let runId: String; let status: String; let answer: String; let products: [Product]; let trace: [ToolEvent];let uiActions:[UIAction]? }
struct ToolEvent: Decodable, Identifiable { var id: Int { index }; let index: Int; let tool: String; let status: String }
struct TryOnJob: Decodable { let jobId: String; let status: String?; let generatedImageUrl: String?; let error: APIMessage?; let notice: String? }
struct Advice: Decodable { let advice: String }
struct PaletteColor: Decodable, Identifiable { var id: String { name }; let name: String; let hex: String }
struct Palette: Decodable { let colors: [PaletteColor]; let explanation: String }
struct EmptyResult: Decodable {}
struct UploadedFile { let field: String; let data: Data }

struct OutfitResult: Decodable { let items:[Ranked]; let knownTotal:Double?; let warnings:[String]? }
struct Avatar: Decodable { let svg:String; let explanation:String; let notice:String }

struct GarmentLabels:Decodable {let title:String;let category:String;let colors:[String];let aesthetics:[String];let fit:String;let uncertainty:[String]}
struct GarmentAnalysisResult:Decodable {let suggestedLabels:GarmentLabels}

enum AppTab:Hashable {case discover,wardrobe,saved,profile}
struct Insights:Decodable {let interactions:[String:Int];let wardrobeCount:Int}
struct UIAction:Decodable {let type:String;let feature:String?;let productId:String?;let action:String?}
