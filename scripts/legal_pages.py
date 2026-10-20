"""Store policy pages (privacy, shipping, returns, terms). Content only; build_seo.py renders them.

Seller details are the ones already published: Alaina is distributed by Mahajan Motors India
(parentOrganization in the homepage JSON-LD), and the GSTIN and Kashmere Gate address are the ones on
mahajanmotorsindia.com.
"""

UPDATED = "20 October 2026"
SELLER = "Mahajan Motors India"
GSTIN = "07AAFFM4750J1Z5"
ADDRESS = "Kashmere Gate, Delhi, India"
PHONE = "+91 79825 55636"
TEL = "+917982555636"
EMAIL = "adhyanmahajan26@gmail.com"
HOURS = "Monday to Saturday, 10:00 to 19:00 IST"

CONTACT_HTML = (
    f"<p>Alaina Shockers, sold and distributed by {SELLER}, {ADDRESS}. GSTIN {GSTIN}.<br/>"
    f'Email: <a href="mailto:{EMAIL}">{EMAIL}</a> · Phone / WhatsApp: <a href="tel:{TEL}">{PHONE}</a><br/>'
    f"{HOURS}.</p>"
)

GRIEVANCE_HTML = (
    f'<p>Write to our Grievance Officer at <a href="mailto:{EMAIL}">{EMAIL}</a> or call '
    f'<a href="tel:{TEL}">{PHONE}</a>. We acknowledge complaints within 48 hours and aim to resolve them within 30 days.</p>'
)

LEGAL_LINKS = [
    ("Privacy policy", "/privacy-policy/"),
    ("Shipping & delivery", "/shipping-policy/"),
    ("Returns & refunds", "/returns-policy/"),
    ("Terms", "/terms/"),
]

PAGES = [
    dict(
        path="/privacy-policy/",
        title="Privacy Policy | Alaina Shockers",
        h1="Privacy policy",
        description="How Alaina Shockers and Mahajan Motors India handle personal data from WhatsApp enquiries and orders. Your rights and Grievance Officer contact.",
        lead=(
            f"alainashockabsorbers.com is the catalogue of Alaina Shockers, sold and distributed by {SELLER} "
            f"(GSTIN {GSTIN}). This policy explains what personal data we handle, why, and the choices you have. "
            "It is written to follow the Digital Personal Data Protection Act, 2023 and the Information Technology Act, 2000 and its rules."
        ),
        sections=[
            ("The short version",
             "<p>The website has no user accounts, takes no payments and has no customer database. We only receive personal data "
             "that you choose to send us by WhatsApp, email or phone. We use it to answer you and fulfil your order. "
             "We do not sell it or use it for third-party advertising.</p>"),
            ("Information you send us",
             "<ul>"
             "<li><strong>Enquiry form.</strong> The Get a quote form does not send anything by itself. It opens WhatsApp with a "
             "message holding what you typed (name, phone number, product line and requirement). Nothing reaches us until you press send.</li>"
             f"<li><strong>WhatsApp.</strong> Buttons across the site open a chat with {PHONE}. Your number and messages are then also "
             "handled by WhatsApp under its own terms and privacy policy.</li>"
             "<li><strong>Orders.</strong> To deliver an order we ask for your name, phone number, delivery address and, for business "
             "buyers, your GSTIN.</li>"
             "<li><strong>Phone and email.</strong> If you call or write to us, we see your number or address and what you tell us.</li>"
             "</ul>"),
            ("Why we use it",
             "<p>We process your data on the basis of your consent, given when you contact us, and for legitimate uses allowed by law. "
             "We use it only to reply to your enquiry and share availability, prices and fitment advice; to confirm, invoice, pack, ship "
             "and support your order, including returns and warranty claims; and to keep the business, accounting and GST records the "
             "law requires. We do not send marketing messages unless you ask for them.</p>"),
            ("Who we share it with",
             "<ul>"
             "<li>Courier and transport companies, who get the name, phone number and address needed to deliver your parts.</li>"
             "<li>Our accountants and tax authorities, where GST and accounting law requires it.</li>"
             "<li>Anyone we are legally required to disclose it to, such as a court or government authority.</li>"
             "</ul><p>We do not sell, rent or trade personal data.</p>"),
            ("Information stored in your browser",
             "<p>The site does not use advertising or analytics cookies. It remembers your light or dark theme choice in your own "
             "browser. That setting stays on your device and is never sent to us.</p>"),
            ("Third-party services",
             "<ul>"
             "<li>Fonts are loaded from Google Fonts, so your browser contacts Google's servers when pages load.</li>"
             "<li>Our web host may keep standard server logs (such as IP address, browser type and pages requested) for security and operation.</li>"
             "<li>WhatsApp and your email provider handle messages you send through them.</li>"
             "</ul>"),
            ("How long we keep it",
             "<p>We keep enquiry messages only as long as needed to serve you. Order and invoice records are kept for as long as GST "
             "and tax law requires, and then deleted.</p>"),
            ("Your rights",
             "<p>You can ask us to tell you what personal data we hold about you, to correct or update it, or to delete it, and you can "
             "withdraw your consent at any time. You can also name another person to exercise these rights for you if you are unable to. "
             "We will do what you ask unless the law requires us to keep a record.</p>"),
            ("Security",
             "<p>We limit access to customer details to the people who need them to serve you. Please never send card numbers, "
             "passwords or OTPs to us on any channel. We will never ask for them.</p>"),
            ("Children",
             "<p>The site is meant for trade buyers and adult vehicle owners. We do not knowingly collect data from anyone under 18.</p>"),
            ("Grievance Officer",
             GRIEVANCE_HTML.replace("</p>", " If you are not satisfied, you may complain to the Data Protection Board of India.</p>")),
            ("Changes", f"<p>We may update this policy as the site or the law changes. Last updated: {UPDATED}.</p>"),
            ("Contact", CONTACT_HTML),
        ],
    ),
    dict(
        path="/shipping-policy/",
        title="Shipping & Delivery Policy | Alaina Shockers",
        h1="Shipping & delivery",
        description="Alaina cabin dampers, shockers and struts ship across India from Delhi. Stock items usually dispatch in 2 working days; delivery typically 2 to 7 days.",
        lead=f"How Alaina Shockers orders are dispatched and delivered by {SELLER}.",
        sections=[
            ("Where we deliver",
             "<p>We ship across India from Kashmere Gate, Delhi, by courier or road transport depending on the size and weight of the "
             "order.</p>"),
            ("Order confirmation",
             "<p>When you send an enquiry on WhatsApp, we confirm the part numbers in stock, the final price including GST, the shipping "
             "charge and the expected dispatch date. Your order is confirmed once you accept that quote and payment is made.</p>"),
            ("Dispatch time",
             "<p>In-stock parts are usually dispatched within 2 working days of order confirmation. Working days are Monday to Saturday, "
             "excluding public holidays. If a part needs to be sourced, we tell you the expected time before you pay.</p>"),
            ("Delivery time",
             "<p>After dispatch, delivery usually takes 2 to 7 working days depending on your location and the carrier. Remote areas and "
             "heavy consignments sent by road can take longer. These times are estimates, not guarantees. We send you the courier name and "
             "tracking or LR (lorry receipt) number once the parcel is dispatched.</p>"),
            ("Shipping charges",
             "<p>Shipping is charged at actual cost based on weight, size and destination, and is shown in your quote before you pay. "
             "Any free-shipping offer will be stated clearly in that quote.</p>"),
            ("Receiving your parcel",
             '<p>Please check the parcel when it arrives. If the packing is torn, wet or tampered with, note it on the delivery receipt '
             'and send us photos on WhatsApp within 48 hours of delivery. See our <a href="/returns-policy/">returns &amp; refunds policy</a>.</p>'),
            ("Delays and wrong addresses",
             "<p>We are not responsible for delays caused by carriers, weather, strikes or other events outside our control, but we will "
             "follow up with the carrier for you. If a parcel comes back because the address or phone number was wrong or nobody accepted "
             "it, we can re-ship it once the extra shipping charge is paid.</p>"),
            ("Contact", CONTACT_HTML),
        ],
    ),
    dict(
        path="/returns-policy/",
        title="Returns & Refunds Policy | Alaina Shockers",
        h1="Returns & refunds",
        description="7-day returns on unused Alaina parts in original packaging, free replacement for wrong or damaged items, refunds usually within 7 working days.",
        lead=f"Return, replacement, cancellation and refund policy for Alaina Shockers parts bought from {SELLER}.",
        sections=[
            ("Return window",
             "<p>You can request a return within 7 days of delivery. Message us on WhatsApp or email with your invoice number, the part "
             "number, the reason and clear photos of the part and its packaging. Please do not send anything back before we confirm the "
             "return and the return address.</p>"),
            ("What we accept",
             "<ul>"
             "<li><strong>Wrong part sent by us, damaged in transit, or faulty on arrival.</strong> We replace it or refund it in full, "
             "including shipping both ways. Transit damage must be reported within 48 hours of delivery with photos.</li>"
             "<li><strong>Wrong part ordered by you, or no longer needed.</strong> Accepted if the part is unused, not fitted, and in its "
             "original, undamaged box with all labels and fittings. Return shipping is paid by you, and the original shipping charge is not refunded.</li>"
             "</ul>"),
            ("What we cannot accept",
             "<ul>"
             "<li>Parts that have been fitted, used, tampered with or damaged after delivery.</li>"
             "<li>Parts without their original packaging, or with the box written on or damaged.</li>"
             "<li>Parts sourced specially for your order, when we told you before you paid that they are non-returnable.</li>"
             "<li>Part of a set. Parts sold as a set, such as dicky shockers or bonnet shockers, can only be returned as the full set.</li>"
             "<li>Requests made after the 7-day window.</li>"
             "</ul>"
             "<p>Please confirm the OE number or send a photo of the old unit before ordering. We are happy to check fitment on WhatsApp.</p>"),
            ("Defects after fitting",
             "<p>If a part fails after fitting because of a manufacturing defect, contact us with your invoice and photos. We may need to "
             "inspect the part before offering a replacement or repair.</p>"),
            ("Cancellations",
             "<p>You can cancel an order at no charge any time before it is dispatched, and we refund any amount paid in full. Once "
             "dispatched, the return rules above apply. If we cannot supply a part after you have paid, we tell you straight away and refund it in full.</p>"),
            ("Refunds",
             "<p>Once the returned part reaches us and passes inspection, we usually issue the refund within 7 working days to the original payment "
             "method or to your bank account by bank transfer or UPI. For GST-registered buyers we issue a credit note against the original invoice.</p>"),
            ("Complaints", GRIEVANCE_HTML),
            ("Contact", CONTACT_HTML),
        ],
    ),
    dict(
        path="/terms/",
        title="Terms of Use | Alaina Shockers",
        h1="Terms of use",
        description="Terms of use and sale for alainashockabsorbers.com: ordering on WhatsApp, prices with GST, payment, fitment and liability. Mahajan Motors India.",
        lead="By using alainashockabsorbers.com or ordering Alaina parts from us you agree to these terms. They are written to be short and plain.",
        sections=[
            ("About the site",
             f"<p>This site is the catalogue of Alaina Shockers, sold and distributed by {SELLER} (GSTIN {GSTIN}), {ADDRESS}. "
             "The website itself does not take payments. You enquire on WhatsApp, phone or email, and an order becomes binding once we "
             'confirm it and payment is made, as set out in our <a href="/shipping-policy/">shipping &amp; delivery policy</a>.</p>'),
            ("Prices and availability",
             "<p>Prices are quoted in Indian rupees and include GST unless stated otherwise. Prices, availability and specifications can "
             "change without notice, and a catalogue listing is not a guarantee of stock. Every order comes with a GST invoice.</p>"),
            ("Payment",
             f"<p>We share payment details when we confirm your order. Only pay to account details sent from our official number {PHONE} "
             "or email.</p>"),
            ("Fitment and OE references",
             "<p>Applications and OE references in the catalogue are a guide. Check your vehicle model and variant, or the OE number on the "
             "old unit, with us before purchase.</p>"),
            ("Delivery, returns and privacy",
             '<p>Delivery is covered by our <a href="/shipping-policy/">shipping &amp; delivery policy</a>, returns, cancellations and '
             'refunds by our <a href="/returns-policy/">returns &amp; refunds policy</a>, and personal data by our '
             '<a href="/privacy-policy/">privacy policy</a>.</p>'),
            ("Brands and content",
             "<p>Vehicle makers' names such as Tata, Ashok Leyland, Eicher, BharatBenz, Mahindra and Toyota are used only to describe "
             "fitment and belong to their owners. Photos and catalogue content on this site may not be copied for commercial use without our permission.</p>"),
            ("Liability",
             "<p>We work to keep the catalogue accurate, but it is provided as is. To the extent allowed by law, our liability for any order "
             "is limited to the amount you paid for it, and we are not liable for indirect losses. Nothing here limits your rights under the "
             "Consumer Protection Act, 2019.</p>"),
            ("Law", "<p>These terms are governed by the laws of India. Courts at Delhi have jurisdiction.</p>"),
            ("Contact", CONTACT_HTML),
        ],
    ),
]
