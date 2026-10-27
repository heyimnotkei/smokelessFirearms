using Vintagestory.API.Common;

namespace LeverAction;

public class LeverActionModSystem : ModSystem
{
    public override void Start(ICoreAPI api)
    {
        // Referenced from itemtypes/leveraction.json as "class": "LeverAction:Repeater"
        api.RegisterItemClass("LeverAction:Repeater", typeof(RepeaterItem));
        api.RegisterItemClass("LeverAction:AK47", typeof(Ak47Item));
    }
}
