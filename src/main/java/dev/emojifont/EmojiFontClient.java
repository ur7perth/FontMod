package dev.emojifont;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.resource.ResourceManagerHelper;
import net.fabricmc.fabric.api.resource.ResourcePackActivationType;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.util.Identifier;

public final class EmojiFontClient implements ClientModInitializer {

    @Override
    public void onInitializeClient() {
        FabricLoader.getInstance()
            .getModContainer("emojifont")
            .ifPresent(container ->
                ResourceManagerHelper.registerBuiltinResourcePack(
                    new Identifier("emojifont", "emoji_font"),
                    container,
                    ResourcePackActivationType.DEFAULT
                )
            );
    }
}
