# AdipoDelivers Premium Rebuild v8

This rebuild converts the control centre from a basic CRUD dashboard into a project-first Field & Impact Studio.

## What changed

- Batch upload multiple photos/videos to one project.
- Project Studio combines narrative, delivery facts, publication controls and field gallery.
- First uploaded image becomes project cover; another image can be made cover later.
- Media can be removed from the project workspace.
- Project source is explicit: manual, imported update or seeded starter record.
- Story priority: standard, featured or flagship.
- Project portfolio now uses visual cards rather than a plain table.
- Command Centre has a field-operations workflow and fast actions.
- Field Media is organised around projects.
- Seeded records are explicitly marked as seeded instead of looking like staff-created records.
- Seed text no longer uses public-facing phrases such as “submitted project photograph”.
- Latest Impact Pulse TV files and cleaned public homepage are included.

## Deploy

1. Replace the corresponding repository files with this package.
2. Commit and push.
3. Render pre-deploy should run `python manage.py migrate`.
4. Confirm migration `impact.0007_premium_project_studio` is applied.
5. Open `/control/projects/`, select a project and test batch media upload.

## Existing production data

Migration 0007 marks the known starter records `WEST-ROAD-001` and `WANG-EDU-001` as `seeded`.
It does not delete any project or media records.

## AWS media

The rebuild continues using the existing S3/CloudFront media storage. No public bucket access is required.
