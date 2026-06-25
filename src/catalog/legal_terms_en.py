from .legal_content import section, paragraph, bullets, email_block

def _terms_sections_en() -> list[dict]:
    return [
        section(
            "general",
            "1. General provisions",
            paragraph("These Terms of Use govern access to the KidsMap site at https://kidsmap.az, and the use of its features, including the catalog, events, user dashboards, reviews, ratings, favorites, ownership requests, and owner functions."),
            paragraph("By using the site, creating an account, or submitting a form, the user confirms that they have read and agree to be bound by these Terms."),
            paragraph("If the user does not agree with the Terms, they must stop using the site features that require acceptance of these Terms."),
            paragraph("The mandatory rights of users provided by the legislation of the Republic of Azerbaijan are not limited by this document.")
        ),
        section(
            "purpose",
            "2. Purpose of KidsMap",
            paragraph("KidsMap is an information platform and a catalog of kids':"),
            bullets(
                "clubs;",
                "sports sections;",
                "educational courses;",
                "creative classes;",
                "specialists;",
                "organizations;",
                "events."
            ),
            paragraph("KidsMap provides the technical capability to find, view, compare, and save information, as well as to contact the respective organizations."),
            paragraph("Unless expressly stated otherwise, KidsMap:"),
            bullets(
                "is not the organizer of classes and events;",
                "does not provide services on behalf of the listed organizations;",
                "is not the employer of trainers or teachers;",
                "is not the agent or representative of the listing owners;",
                "is not a party to the contract between the user and the organization;",
                "does not make decisions on a child's enrollment;",
                "is not responsible for the provision of classes by the organization to the extent permitted by law."
            ),
            paragraph("Agreements on classes, payment, refunds, attendance, security, and other conditions arise directly between the user and the chosen organization unless KidsMap expressly states otherwise.")
        ),
        section(
            "accuracy",
            "3. Accuracy of information",
            paragraph("KidsMap strives to keep information up to date but cannot guarantee the absolute accuracy of all data provided by organizations and users."),
            paragraph("Before enrolling or paying, the user is advised to independently confirm:"),
            bullets(
                "current price;",
                "schedule;",
                "age restrictions;",
                "availability of places;",
                "address;",
                "qualifications of specialists;",
                "necessary licenses and permits;",
                "attendance rules;",
                "cancellation and refund conditions;",
                "safety requirements."
            ),
            paragraph("If a user finds an error, they can report it to:"),
            email_block("kidsmap.az@gmail.com"),
            paragraph("Nothing in this section releases KidsMap from liability that cannot be excluded by law.")
        ),
        section(
            "badges",
            "4. Verification badges",
            paragraph("If badges like 'Verified by KidsMap', 'Owner Confirmed', or similar statuses are used on the site, the meaning of each badge is determined by the actual verification performed (for example, basic confirmation of the user's connection with the organization via contact phone or email)."),
            paragraph("Such a badge does not automatically mean:"),
            bullets(
                "state accreditation;",
                "the presence of all possible licenses;",
                "verification of every employee;",
                "guaranteed quality of services;",
                "guaranteed safety;",
                "recommendation on behalf of a state body."
            )
        ),
        section(
            "users-and-age",
            "5. Users and age",
            paragraph("The site is primarily intended for adult users, parents, legal guardians of children, and representatives of organizations."),
            paragraph("A minor must not independently:"),
            bullets(
                "create an owner account;",
                "apply to manage an organization;",
                "publish personal data;",
                "assume obligations;",
                "enter into paid agreements,"
            ),
            paragraph("if the consent or participation of a legal guardian is required for this."),
            paragraph("The user agrees to provide accurate information and to use the site with the participation of a legal guardian when required by law.")
        ),
        section(
            "registration",
            "6. Registration and account",
            paragraph("Registration may be required for certain features."),
            paragraph("The user must:"),
            bullets(
                "provide accurate information;",
                "use an email address belonging to them;",
                "not impersonate another person;",
                "ensure the confidentiality of login details;",
                "not transfer the account to third parties;",
                "report unauthorized access;",
                "promptly update data."
            ),
            paragraph("The user is responsible for actions taken through their account unless otherwise established by law or caused by a breach by KidsMap."),
            paragraph("KidsMap has the right to temporarily restrict access to the account if there is a reasonable suspicion of hacking, fraud, spam, abuse, violation of these Terms, or a threat to user security.")
        ),
        section(
            "roles",
            "7. User roles",
            paragraph("A newly registered user is created as a regular user."),
            paragraph("The ability to manage a listing is granted after the approval of an ownership request or the granting of appropriate rights through the system-provided process."),
            paragraph("Obtaining the owner role does not mean transferring ownership rights to KidsMap, confirming all user statements, issuing a license by a state body, or automatically approving all future publications.")
        ),
        section(
            "ownership",
            "8. Ownership requests",
            paragraph("A user applying to manage a listing confirms that they:"),
            bullets(
                "have a legal connection with the organization;",
                "have the right to represent the organization or have the appropriate permission;",
                "provide accurate information;",
                "are not trying to gain access to someone else's organization fraudulently."
            ),
            paragraph("KidsMap has the right to:"),
            bullets(
                "request confirmation of authority;",
                "request additional information;",
                "contact the organization;",
                "reject the application;",
                "revoke previously granted access;",
                "transfer management to another confirmed representative;",
                "save the history of decisions for security and audit purposes."
            ),
            paragraph("Providing false documents or information may result in account blocking and other consequences provided by law.")
        ),
        section(
            "team",
            "9. Owner team",
            paragraph("The owner can invite other users to the team if such a feature is provided by the system."),
            paragraph("The person sending the invitation must use a correct email, invite only authorized persons, assign the minimum necessary rights, and revoke access for persons who no longer represent the organization."),
            paragraph("A team member must use their rights only within the granted role. KidsMap has the right to restrict access to a team member in case of security breaches or violations of these Terms.")
        ),
        section(
            "content-management",
            "10. Creating and editing listings",
            paragraph("The owner or other authorized user is responsible for the accuracy of the posted information."),
            paragraph("It is prohibited to publish:"),
            bullets(
                "fictitious organizations and services;",
                "false prices;",
                "misleading discounts;",
                "someone else's contact details without justification;",
                "information violating the rights of third parties;",
                "materials prohibited by law."
            ),
            paragraph("Information can be saved as a draft, sent for moderation, rejected, published, unpublished, temporarily hidden, deleted, or archived."),
            paragraph("Moderation does not mean a full legal, financial, or professional audit of the organization.")
        ),
        section(
            "pricing",
            "11. Prices, schedule, and offers",
            paragraph("The organization must keep published prices, schedules, and conditions up to date."),
            paragraph("If the price depends on age, duration, branch, package, etc., this must be stated clearly and without misleading the user."),
            paragraph("Phrases like 'free', 'discount', 'best price', 'guaranteed result' and similar statements must have a factual basis.")
        ),
        section(
            "events",
            "12. Events",
            paragraph("The event organizer is responsible for the date, time, location, age restrictions, cost, ticket availability, cancellation, rescheduling, attendance rules, security, and refunds if applicable."),
            paragraph("KidsMap is not responsible for the cancellation or change of an event by an independent organizer, except where expressly provided by law or specific KidsMap conditions.")
        ),
        section(
            "reviews",
            "13. Reviews, ratings, and reactions",
            paragraph("A user may publish a review only based on their own good-faith experience or reliable information."),
            paragraph("The following are prohibited:"),
            bullets(
                "fake commissioned reviews and mass artificial rating manipulation;",
                "publishing reviews by competitors to cause harm;",
                "threats, insults, discriminatory remarks;",
                "disclosure of personal data and information about a child without reason;",
                "spam, advertising, extortion, and illegal materials."
            ),
            paragraph("KidsMap has the right to moderate, hide, or delete a review. The deletion of a review does not mean KidsMap recognizes any party to a dispute."),
            paragraph("The organization has the right to file a justified complaint but cannot demand the removal of a negative review simply because it is negative.")
        ),
        section(
            "children-materials",
            "14. Photos and materials involving children",
            paragraph("It is prohibited to upload a photo, video, or other materials depicting a child without the necessary rights and permissions."),
            paragraph("The user uploading the material confirms that they:"),
            bullets(
                "have the right to use it;",
                "have obtained the necessary consent from the parent or legal guardian;",
                "the publication does not threaten the child's safety;",
                "the material does not contain degrading, harmful, or illegal content."
            ),
            paragraph("It is prohibited to publish materials revealing a child's address, contact details, medical information, exact route, and other sensitive information."),
            paragraph("KidsMap has the right to immediately hide the material until a complaint check is completed. Removal requests should be sent to:"),
            email_block("kidsmap.az@gmail.com")
        ),
        section(
            "prohibited-content",
            "15. Prohibited content",
            paragraph("The user is prohibited from posting or distributing content prohibited by law, calls for violence, child exploitation, pornographic materials, threats, malicious code, spam, automated mass publications, and illegal offers."),
            paragraph("KidsMap has the right to delete or restrict access to such material, and in cases provided by law, transmit information to competent authorities.")
        ),
        section(
            "intellectual-property",
            "16. KidsMap Intellectual Property",
            paragraph("Rights to the KidsMap name, logo, design, source code, site structure, original texts, graphic elements, and database compilation belong to the respective right holders."),
            paragraph("Without permission, it is prohibited to:"),
            bullets(
                "copy a substantial part of the catalog;",
                "use automated scraping;",
                "copy the design or impersonate KidsMap;",
                "bypass technical restrictions."
            ),
            paragraph("Normal use of public pages by the user for personal non-commercial purposes is permitted within the site's functionality and legislation.")
        ),
        section(
            "user-content",
            "17. User content",
            paragraph("The user retains rights to the content belonging to them."),
            paragraph("By uploading content, the user grants KidsMap a non-exclusive, royalty-free right to use it only to the extent necessary for storage, technical processing, display on the site, adaptation, moderation, translation, and promotion of a specific KidsMap listing."),
            paragraph("This permission is valid as long as the material is posted on the site, and after deletion — only within technical backups, audit logs, and mandatory legal requirements.")
        ),
        section(
            "complaints",
            "18. Complaints about rights violations",
            paragraph("Complaints can be sent to:"),
            email_block("kidsmap.az@gmail.com"),
            paragraph("The complaint should preferably include the applicant's name, contact email, link to the material, description of the violation, and the requested action."),
            paragraph("KidsMap may request additional information and temporarily hide the disputed material during the review. A knowingly false complaint may be considered abuse.")
        ),
        section(
            "advertising",
            "19. Advertising and promoted listings",
            paragraph("If VIP placements, promotional listings, sponsored materials, or paid boosting are used on the site, they are separated from regular content and clearly marked."),
            paragraph("Advertising materials must not mislead the user, hide their advertising nature, or misuse children's information.")
        ),
        section(
            "paid-services",
            "20. Paid services",
            paragraph("In the current version of the site, online payment via KidsMap is not implemented."),
            paragraph("If paid features are introduced in the future, separate clear terms of payment, refunds, and service provision will apply before payment is made.")
        ),
        section(
            "third-parties",
            "21. Third-party organizations and links",
            paragraph("The site may contain links to external resources, social networks, and booking systems. When navigating to a third-party resource, the user interacts with the respective owner independently."),
            paragraph("KidsMap does not control the availability of a third-party site, its rules, data processing, prices, or security.")
        ),
        section(
            "privacy",
            "22. Personal data",
            paragraph("The processing of personal data is governed by a separate KidsMap Privacy Policy."),
            paragraph("In case of a conflict between these Terms and the Privacy Policy, personal data processing issues are governed by the Privacy Policy and mandatory legal norms.")
        ),
        section(
            "availability",
            "23. Site availability",
            paragraph("KidsMap strives to ensure stable operation, but technical maintenance, failures, restrictions of third-party services, and other circumstances are possible."),
            paragraph("KidsMap does not guarantee uninterrupted and error-free operation of the site, but undertakes to take reasonable measures to fix known critical errors and ensure security.")
        ),
        section(
            "security",
            "24. Security",
            paragraph("It is prohibited to attempt to gain unauthorized access, guess passwords, upload malicious code, mass collect data in violation of technical limits, or bypass the moderation flow."),
            paragraph("KidsMap has the right to restrict access and save technical details of the incident.")
        ),
        section(
            "suspension",
            "25. Suspension and termination of access",
            paragraph("KidsMap has the right to restrict or terminate user access in case of a material violation of the Terms, fraud, security threat, illegal content upload, or a lawful request from a competent authority."),
            paragraph("When possible and when it does not pose a threat, the user may be provided with information about the reason for the restriction.")
        ),
        section(
            "deletion",
            "26. Account deletion",
            paragraph("The user can send a request to delete their account to:"),
            email_block("kidsmap.az@gmail.com"),
            paragraph("Account deletion does not always mean the immediate physical deletion of every record. Some data may be retained within limits provided by law for audit, security, dispute resolution, and maintaining database integrity.")
        ),
        section(
            "liability",
            "27. Limitation of liability",
            paragraph("To the extent permitted by law:"),
            bullets(
                "KidsMap is not responsible for the actions of independent organizations;",
                "KidsMap is not responsible for user decisions made based on third-party information;",
                "KidsMap does not guarantee a specific educational, sports, or other outcome;",
                "KidsMap is not responsible for changes in conditions by an organization without notifying the platform."
            ),
            paragraph("No provision of the Terms excludes liability that cannot be excluded by law, mandatory consumer rights, or liability for intentional unlawful actions.")
        ),
        section(
            "user-liability",
            "28. User liability",
            paragraph("The user is responsible for the legality of their actions, the accuracy of the provided information, the posted content, the possession of permissions, and the security of their account."),
            paragraph("If the user's actions caused confirmed damage, compensation is resolved in accordance with the law.")
        ),
        section(
            "changes",
            "29. Changes to the site",
            paragraph("KidsMap has the right to improve the interface, add or remove features, and change categories and moderation rules."),
            paragraph("Substantial changes affecting user rights will not be applied secretly or retroactively to the detriment of mandatory rights.")
        ),
        section(
            "terms-changes",
            "30. Changes to the Terms",
            paragraph("The current version is published on this page. For significant changes, users may be notified via the site, dashboard, or email."),
            paragraph("Continued use after notification may constitute acceptance of the new version only to the extent permitted by law.")
        ),
        section(
            "disputes",
            "31. Dispute resolution",
            paragraph("The user may first send an appeal to:"),
            email_block("kidsmap.az@gmail.com"),
            paragraph("The parties shall strive to settle the dispute through negotiations. This does not limit the user's right to apply to a competent state body or court.")
        ),
        section(
            "applicable-law",
            "32. Applicable law",
            paragraph("These Terms are governed by the laws of the Republic of Azerbaijan."),
            paragraph("If the user has mandatory rights under applicable law, these Terms do not limit such rights.")
        ),
        section(
            "severability",
            "33. Severability",
            paragraph("If any individual provision is found to be invalid or unenforceable, the remaining provisions shall continue in effect to the extent permitted by law.")
        ),
        section(
            "contacts",
            "34. Contacts",
            paragraph("For questions about using the site, complaints, listings, accounts, and content, contact:"),
            email_block("kidsmap.az@gmail.com")
        )
    ]
