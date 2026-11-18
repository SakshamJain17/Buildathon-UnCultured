import Foundation
import Security

struct AppError: LocalizedError { let message: String; var errorDescription: String? { message } }

@MainActor
final class API {
    var baseURL: String
    var token: String = ""
    init(baseURL: String) { self.baseURL = baseURL }
    func request<T: Decodable>(_ path: String, method: String = "GET", body: [String: Any]? = nil, idempotency: String? = nil) async throws -> T {
        guard let url = URL(string: baseURL + "/api/v1" + path), let scheme = url.scheme, ["http", "https"].contains(scheme) else { throw AppError(message: "Enter a valid backend URL.") }
        var req = URLRequest(url: url); req.httpMethod = method; req.timeoutInterval = 100
        if !token.isEmpty { req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }
        if let idempotency { req.setValue(idempotency, forHTTPHeaderField: "Idempotency-Key") }
        if let body { req.httpBody = try JSONSerialization.data(withJSONObject: body); req.setValue("application/json", forHTTPHeaderField: "Content-Type") }
        return try decode(try await URLSession.shared.data(for: req))
    }
    func upload<T: Decodable>(_ path: String, fields: [String: String], files: [UploadedFile], idempotency: String? = nil) async throws -> T {
        guard let url = URL(string: baseURL + "/api/v1" + path) else { throw AppError(message: "Invalid backend URL.") }
        let boundary = "allure-" + UUID().uuidString
        var req = URLRequest(url: url); req.httpMethod = "POST"; req.timeoutInterval = 100
        req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        req.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        if let idempotency { req.setValue(idempotency, forHTTPHeaderField: "Idempotency-Key") }
        var data = Data()
        func append(_ text: String) { data.append(Data(text.utf8)) }
        for (key, value) in fields { append("--\(boundary)\r\nContent-Disposition: form-data; name=\"\(key)\"\r\n\r\n\(value)\r\n") }
        for file in files {
            append("--\(boundary)\r\nContent-Disposition: form-data; name=\"\(file.field)\"; filename=\"photo.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n")
            data.append(file.data); append("\r\n")
        }
        append("--\(boundary)--\r\n"); req.httpBody = data
        return try decode(try await URLSession.shared.data(for: req))
    }
    func image(_ id: String) async throws -> Data {
        guard let url = URL(string: baseURL + "/api/v1/wardrobe/\(id)/image") else { throw AppError(message: "Invalid image URL.") }
        var request = URLRequest(url: url); request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        let (data, response) = try await URLSession.shared.data(for: request)
        guard (response as? HTTPURLResponse)?.statusCode == 200 else { throw AppError(message: "Could not load wardrobe image.") }; return data
    }
    private func decode<T: Decodable>(_ result: (Data, URLResponse)) throws -> T {
        let decoder = JSONDecoder(); decoder.keyDecodingStrategy = .convertFromSnakeCase
        let envelope = try decoder.decode(Envelope<T>.self, from: result.0)
        if envelope.error?.code == "UNAUTHORIZED" { throw AppError(message: "Your session expired. Sign out and start a new session.") }
        guard envelope.success, let data = envelope.data else { throw AppError(message: envelope.error?.message ?? "Request failed.") }
        return data
    }
}

// Session token is stored in Keychain, never UserDefaults or source control.
enum Vault {
    static func save(_ token: String, account: String) {
        let query: [String: Any] = [kSecClass as String:kSecClassGenericPassword,kSecAttrService as String:"allure-session",kSecAttrAccount as String:account]
        SecItemDelete(query as CFDictionary)
        var item = query; item[kSecValueData as String] = Data(token.utf8); item[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        SecItemAdd(item as CFDictionary, nil)
    }
    static func load(account: String) -> String {
        let query: [String: Any] = [kSecClass as String:kSecClassGenericPassword,kSecAttrService as String:"allure-session",kSecAttrAccount as String:account,kSecReturnData as String:true,kSecMatchLimit as String:kSecMatchLimitOne]
        var result: CFTypeRef?; guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess, let data = result as? Data else { return "" }
        return String(data:data,encoding:.utf8) ?? ""
    }
}
