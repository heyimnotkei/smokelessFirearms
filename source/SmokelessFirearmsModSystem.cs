using Vintagestory.API.Common;

namespace SmokelessFirearms;

public class SmokelessFirearmsModSystem : ModSystem
{
    public override void Start(ICoreAPI api)
    {
        // Referenced from itemtypes/leveraction.json as "class": "SmokelessFirearms:Repeater"
        api.RegisterItemClass("SmokelessFirearms:Repeater", typeof(RepeaterItem));
        api.RegisterItemClass("SmokelessFirearms:AK47", typeof(Ak47Item));
    }
}
