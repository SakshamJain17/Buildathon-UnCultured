import Foundation

@main struct VerifyAPI {
    @MainActor static func main() async throws {
        let api=API(baseURL:"http://127.0.0.1:8766")
        let session:Session=try await api.request("/sessions",method:"POST",body:["name":"Swift integration test"])
        api.token=session.token
        let me:Profile=try await api.request("/me")
        let feed:Feed=try await api.request("/recommendations")
        guard let item=feed.items.first else {fatalError("Expected catalogue fixtures")}
        let _:EmptyResult=try await api.request("/swipes",method:"POST",body:["product_id":item.id,"action":"dislike"])
        let after:Feed=try await api.request("/recommendations?include_seen=true")
        precondition(!after.items.contains{$0.id==item.id})
        let cities:[City]=try await api.request("/locations/search?q=Gurugram")
        guard let city=cities.first else {fatalError("City not found")}
        let daily:Daily=try await api.request("/stylist/daily",method:"POST",body:["location":["latitude":city.latitude,"longitude":city.longitude]])
        let wardrobe:WardrobeList=try await api.request("/wardrobe")
        let _:EmptyResult=try await api.request("/me",method:"DELETE")
        print("PASS: Swift decoded session, profile, feed, city, daily forecast and wardrobe. Dismissal persisted. Name: \(me.name); source: \(daily.weather.source); wardrobe: \(wardrobe.items.count).")
    }
}
