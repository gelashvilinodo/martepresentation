/*
 * მართეოს პრეზენტაციის პარამეტრები
 * ------------------------------------------------------------
 * ამ ფაილში შეცვალე ბმული, კონტაქტები, რიცხვები და სქრინშოტები.
 * სლაიდების ტექსტი თავად index.html-შია და პირდაპირ იქ რედაქტირდება.
 */
window.MARTEO_CONFIG = {
  // საიტის ბმული - გამოიყენება ბოლო სლაიდზე და QR კოდში.
  // ⚠️ ჩაანაცვლე რეალური მისამართით.
  siteUrl: 'https://marteo.ge',

  // ერთი სლაიდის ხანგრძლივობა მილიწამებში (6000 = 6 წამი).
  slideDuration: 6000,

  // true - პრეზენტაცია გახსნისთანავე იწყება.
  autoplay: true,

  // საიტის სქრინშოტები დემო სლაიდისთვის (მე-5 სლაიდი).
  // ცარიელი დატოვებისას ჩანს ჩაშენებული მაკეტი.
  // მაგ.: laptop: 'assets/screens/desktop.png', phone: 'assets/screens/mobile.png'
  // სასურველია მაღალი (სრული გვერდის) სქრინშოტი - ის ეკრანში ნელა „ისქროლება“.
  screenshots: {
    laptop: '',
    phone: ''
  },

  // კონტაქტები (მე-8 სლაიდი). icon: mail | phone | facebook | instagram | linkedin | globe
  // ⚠️ ჩაანაცვლე რეალური მონაცემებით.
  contacts: [
    { icon: 'mail',      label: 'ელფოსტა',  value: 'info@marteo.ge',    href: 'mailto:info@marteo.ge' },
    { icon: 'phone',     label: 'ტელეფონი', value: '+995 5XX XX XX XX', href: '' },
    { icon: 'facebook',  label: 'Facebook',  value: 'Marteo',            href: '' },
    { icon: 'instagram', label: 'Instagram', value: '@marteo',           href: '' },
    { icon: 'linkedin',  label: 'LinkedIn',  value: 'Marteo',            href: '' }
  ],

  // მთავარი მაჩვენებლები (მე-7 სლაიდი). ცარიელი სიის შემთხვევაში სლაიდი არ ჩანს.
  // მაგალითი:
  // stats: [
  //   { value: 500,  prefix: '',  suffix: '+', label: 'აქტიური ბიზნესი' },
  //   { value: 120000, prefix: '', suffix: '+', label: 'დამუშავებული შეკვეთა' },
  //   { value: 98,   prefix: '',  suffix: '%', label: 'კმაყოფილი მომხმარებელი' }
  // ],
  stats: []
};
