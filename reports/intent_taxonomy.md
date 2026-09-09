# SpotifyCares Intent Taxonomy

## Scope and evidence

The taxonomy is based on the actual `SpotifyCares` customer-message subset in `data/raw/twcs.csv`: **15,096** inbound messages directly linked to a `SpotifyCares` outbound tweet and **8,723** distinct customer accounts. I reviewed the full linked subset through reproducible keyword-supported inspection and manually reviewed representative examples selected from the actual messages. Keyword counts below are exploratory overlapping signals, not labels or evaluation scores.

The taxonomy is deliberately small. A message receives one primary intent during annotation. When multiple problems are present, annotators should choose the problem that blocks the customer's requested outcome; if that cannot be determined, use `other_unclear` and explain why.

## Final intents

### `playback_audio_issue`

**Definition:** Problems with listening behavior or audio playback.

**Belongs:** songs not playing, playback stopping, shuffle/repeat behavior, skipping, buffering, missing sound, or streaming playback failures.

**Does not belong:** a login/password problem (`account_access`), a clearly device/OS-specific compatibility problem (`device_platform_compatibility`), or managing playlists/albums/downloads (`playlist_library_downloads`).

**Real examples:**

- Tweet `850`: “Premium & when i have it on shuffle it turns off when the song is done and just plays in order and the repeat lights up but doesn't repeat”
- Tweet `16210`: “I can log in but I get no sound after selecting play?”
- Tweet `1868`: “I tried it on web browser and it worked!”

### `app_technical_issue`

**Definition:** A general Spotify application malfunction where the device or platform is not the main distinguishing factor.

**Belongs:** the app crashes, fails to load, gives an error, stops working after an update, or remains broken after ordinary troubleshooting.

**Does not belong:** a specifically named platform/device compatibility issue (`device_platform_compatibility`), a playback-only symptom (`playback_audio_issue`), or a product limitation/how-to question (`feature_or_policy_information`).

**Real examples:**

- Tweet `849`: “doesn't work and i even tried deleting the app”
- Tweet `857`: “Yes, multiple times. No changes. I am Premium User ... there should be a bugfree running App”
- Tweet `858`: “there is no way to manage Albums ... in the App. It's a mess”

### `account_access`

**Definition:** Problems identifying, accessing, or recovering a Spotify account.

**Belongs:** login, password, Facebook login, account email, inability to access an account, or account identity confusion.

**Does not belong:** Premium payment/plan status without an access problem (`subscription_plan_billing`) or a generic app error after successful login (`app_technical_issue`).

**Real examples:**

- Tweet `2875`: “I'm using my facebook account as a method to log in.”
- Tweet `8424`: “I login with facebook ... but i think my email account for spotify is my old one ... What can I do?”
- Tweet `36162`: “already tried with an other computer and for the password dont need it im loggin with my facebook account !”

### `subscription_plan_billing`

**Definition:** Questions or problems involving Free/Premium status, subscriptions, payments, charges, refunds, or billing.

**Belongs:** Premium eligibility, plan changes, cancellation, charges, payment processing, refunds, or billing account questions.

**Does not belong:** an app or playback failure that merely mentions Premium, unless the plan or payment is the actual requested outcome.

**Real examples:**

- Tweet `27676`: “So why let non premium customers even select them.? Pointless.”
- Tweet `40657`: “But can I put my account number in so my payment can still comes out”
- Tweet `40660`: “Can my payment still come out”

### `playlist_library_downloads`

**Definition:** Managing or using playlists, albums, saved library content, local files, downloads, or offline content.

**Belongs:** playlist creation or editing, album/library management, imported local files, downloaded content, offline availability, or greyed-out library items.

**Does not belong:** an individual song failing during playback (`playback_audio_issue`) or a general app crash unrelated to library content (`app_technical_issue`).

**Real examples:**

- Tweet `2952`: “What keywords besides 'playlist', 'playlists', + 'song' would I use?”
- Tweet `2949`: “My ... playlists idea's status got changed + can't receive any votes. They sent me a link to a 'similar idea', but it's closed.”
- Tweet `11169`: “They aren't locally imported... We just imported her iTunes playlist in Spotify so it found identical songs. Is that why they are greyed out?”

### `device_platform_compatibility`

**Definition:** A problem explicitly tied to a device, operating system, browser, desktop client, or hardware environment.

**Belongs:** iPhone/iOS, Android, Windows, Mac, browser, desktop client, or speaker-specific compatibility and behavior.

**Does not belong:** a platform-independent app fault (`app_technical_issue`) or a playback symptom where the platform is incidental (`playback_audio_issue`).

**Real examples:**

- Tweet `853`: “iphone 7+ and i have the most recent update for spotify”
- Tweet `1869`: “using a MacBook Pro with OS X El Capitan ... and an iPhone 6S with the latest software/Spotify updates!”
- Tweet `2853`: “... it's working now, but again, it's working now. ... MacOS High Sierra. Looks like version 1.0.68.407...”

### `feature_or_policy_information`

**Definition:** Questions about how a feature works, whether something is available, a product limitation, a policy, or a feature suggestion without a primary malfunction.

**Belongs:** “can I”/“how do I” questions, feature availability, removed-feature complaints, policy explanations, and suggestions.

**Does not belong:** a concrete technical failure that needs troubleshooting (`app_technical_issue`), or a payment/account problem (`subscription_plan_billing` / `account_access`).

**Real examples:**

- Tweet `4995`: “That stinks. Can you make it a feature, off by default, that I can enable?”
- Tweet `4999`: “I used to use that feature as an example of great UX.”
- Tweet `5028`: “Doesn't show in lock screen. Can't adjust volume of phone isn't unlocked also.”

### `other_unclear`

**Definition:** A message that is ambiguous, contains conflicting primary intents, is only a terse context-dependent follow-up, or does not fit the supported taxonomy.

**Belongs:** “yes”, “DM sent”, unexplained screenshots/URLs, multi-intent messages where no primary problem is clear, and unsupported requests.

**Does not belong:** a message that can be assigned consistently using the definitions above.

**Real examples:**

- Tweet `864`: “ok thx”
- Tweet `465263`: “@SpotifyCares ?”
- Tweet `980158`: “@SpotifyCares k”

Tweet `857` is a boundary case: it mentions Premium and an app failure. Annotators should choose the primary requested outcome and record the ambiguity in notes. The golden-set annotator should use only rows produced by `scripts/prepare_intent_candidates.py`.

## Exploratory support signals

In the linked SpotifyCares subset, overlapping lexical signals were observed for playback/audio (2,818), app technical issues (4,910), account access (882), subscription/billing (601), playlists/library/downloads (1,427), device/platform (2,092), and feature/policy language (1,413). These counts helped validate that each proposed area exists in the data, but they are not class counts and must not be reported as classifier performance.

## Manual annotation plan

Run:

```powershell
py -m scripts.prepare_intent_candidates --size 200
```

Review the generated file and fill `intent` and `label_notes` manually. The provided empty [spotifycares_intent_labels.csv](../data/golden/spotifycares_intent_labels.csv) is a schema template; it contains no fabricated labels. The target is 150–250 reviewed examples, including common, rare, terse, ambiguous, and multi-turn cases.

## Leakage prevention

The candidate generator uses only inbound customer messages directly linked to a `SpotifyCares` support tweet. It records `conversation_id` by following `in_response_to_tweet_id` parent links through the full source table. `scripts/train_intent.py` uses `GroupShuffleSplit` on that conversation ID, so messages from one conversation cannot appear in both train and held-out sets. Future company reply text is never included as a classifier feature; training uses only `customer_text`.

## Pending items

No manually labelled golden set, trained model artifact, accuracy, F1, confusion matrix, or evaluation result is claimed in this phase. Those require manual annotation first.