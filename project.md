# Taslamanyň Analizi we App-ler

Bu taslama "Doglanlar Studio" we "Foto Studio" üçin niýetlenen backend bolup, aşakdaky app-lerden ybarat:

## 1. Identity App (Agza Bolmak we Profil)
- **Register/Login**: JWT we OTP goldawy. [x] Edildi.
- **Profile**: Ulanyjy maglumatlary we rollary. [x] Edildi.
- **Status**: [x] Edildi.

## 2. Commerce App (Studio Harytlar)
- **Harytlar we Kategoriýalar**: Haryt katalogy. [x] Edildi.
- **Sargyt Ulgamy (Order System)**: Haryt sargytlary. [x] Edildi.
- **Admin Panel**: Harytlar we sargytlar doly sazlandy. [x] Edildi.
- **Status**: [x] Edildi.

## 3. Blog App (Studio Blog)
- **Mümkinçilikler**: Surat we wideo goldawy bolan blog ýazgylary. [x] Edildi.
- **Status**: [x] Edildi.

## 4. Photo Studio App (Foto Studio Portfoliýasy)
- **Portfoliýa**: Kategoriýalara bölünen foto/wideo bloglar. [x] Edildi.
- **Sargyt Ulgamy**: [DELETE] Ulanyjy talaby boýunça aýryldy.
- **Admin Panel**: Kategoriýalar we bloglar doly sazlandy. [x] Edildi.
- **Status**: [x] Edildi (Bloglar elýeterli).

## 5. Management & Sync (Flutter App üçin)
Flutter "news_app" (Management app) üçin gerekli ähli modeller we API-lar `main` app-da jemlendi.
- **Müşderiler (Customers)**: [x] Edildi.
- **Duşuşyklar (Appointments)**: [x] Edildi.
- **Enjamlar (Equipments)**: [x] Edildi.
- **Çykdajylar (Expenses)**: [x] Edildi.
- **Dolandyryş Sargytlary (Management Orders)**: Çylşyrymly sargyt ulgamy. [x] Edildi.
- **Order Types**: [x] Edildi.
- **Admin Panel**: Ähli dolandyryş modelleri admin panelde sazlandy. [x] Edildi.
- **Status**: [x] Edildi.

---

### Edilen Işler:
- [x] Backend-de täze goşulan `OrderType` üçin admin paneli sazlamak.
- [x] Ähli modelleri (Customer, Appointment, Expense we ş.m.) admin panele goşmak.
- [x] Flutter app üçin API-lary `/api/` prefiksine geçirmek.
- [x] Photo Studio-dan sargyt ulgamyny aýyrmak.
- [x] Backend unit testleri ýazyldy we barlagdan geçdi (24 test).
- [x] Flutter studioapp kody iki bölege (Commerce we Photo Studio) bölündi.
- [x] Programmanyň dizaýny ak fon we gara tekst stilinde täzelendi.

### Edilmeli Işler:
- [ ] Flutter app-yň doly integrasiýasyny manuel barlamak.
