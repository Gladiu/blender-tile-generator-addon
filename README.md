# Blender Tile Generation Addon

## Blender addon development little HOW TO

First we need to install the addon. To install it, we have to generate .zip file with our addons. To do this, in addon repository run:

```bash
blender --command extension build
```

You will get .zip file that can be installed in blender as addon. As of 4.2, You can go in Blender to Edit->Preferences->GetExtensions->Little arrow in top right corner->Install from disk. Select Your .zip file.

Addon will be installed in one of the directories from Edit->Preferences->GetExtensions->Repositories. You can look it up by clicking one of the local repositories and going to Advanced. There You can look up custom directory property.

Once installed and You found the installation directory, You can edit the addon there. Once edited, You have to reload addon in Blender by clicking F3 and from menu select "Reload Scripts". If You wish to have version control, You can copy .git directory to addon installation directory (yea I know it's rough and probably can be done in better way).


## TODOs:

 - [ ] Don't allow removal of all rows in action mixer - if user doesn't want animaction it should be just left to "None"
 - [ ] Camera position restoring is not working
 - [ ] When **no** material is added to the object (only default one is present), addon throws an error
