using CombatOverhaul;
using CombatOverhaul.Animations;
using CombatOverhaul.Implementations;
using CombatOverhaul.Inputs;
using CombatOverhaul.MeleeSystems;
using CombatOverhaul.RangedSystems;
using CombatOverhaul.Utils;
using Firearms;
using OpenTK.Mathematics;
using System.Text;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;
using Vintagestory.API.Server;

namespace LeverAction;

/// <summary>
/// Side-loading tube-magazine repeater, built on Firearmsfork's muzzleloader state machine.
///
/// Mapping of the lever-action onto the existing states:
///   Unloaded  -> hold RMB: one cartridge per pass through the side gate (Load), repeating until the tube is full
///   Loaded    -> hold RMB: work the lever to chamber a round (Prime animation)
///   Primed    -> Cocked (automatic) -> Aim (hold RMB) -> Shoot (LMB)
///   Shoot     -> the shoot animation includes the lever cycle, so the round after it is already chambered
///
/// Differences from the base class, all about being a *repeater*:
///   * releasing RMB part-way through loading keeps the rounds already loaded (Loaded instead of Unloaded)
///   * a new reload session can only start with an empty magazine
/// </summary>
public class RepeaterClient : MuzzleloaderClient
{
    private bool EmptyReloadSession;
    private int Ak47CycleCounter;

    public RepeaterClient(ICoreClientAPI api, Item item) : base(api, item)
    {
    }

    [ActionEventHandler(EnumEntityAction.LeftMouseDown, ActionState.Active)]
    protected override bool ShootAutomatic(ItemSlot slot, EntityPlayer player, ref int state, ActionEventData eventData, bool mainHand, AttackDirection direction)
    {
        if (Item.Code.Path != "ak47") return base.ShootAutomatic(slot, player, ref state, eventData, mainHand, direction);
        return Stats.AutomaticFire && TryShoot(slot, player, ref state, eventData, mainHand);
    }

    protected override bool TryShoot(ItemSlot slot, EntityPlayer player, ref int state, ActionEventData eventData, bool mainHand)
    {
        if (Item.Code.Path != "ak47") return base.TryShoot(slot, player, ref state, eventData, mainHand);
        return TryShootAk47(slot, player, ref state, eventData, mainHand);
    }

    protected override bool TryShootAutomaticContinuation(ItemSlot slot, EntityPlayer player, bool mainHand)
    {
        if (Item.Code.Path != "ak47") return base.TryShootAutomaticContinuation(slot, player, mainHand);
        int state = (int)MuzzleloaderState.Aim;
        return TryShootAk47(slot, player, ref state, default, mainHand, continuation: true);
    }

    private bool TryShootAk47(ItemSlot slot, EntityPlayer player, ref int state, ActionEventData eventData, bool mainHand, bool continuation = false)
    {
        if (!(continuation ? CheckState(mainHand, MuzzleloaderState.Aim) : CheckState(state, MuzzleloaderState.Aim)) || !ShotGateOpen(mainHand)) return false;
        if (!continuation && InteractionsTester.PlayerTriesToInteract(player, mainHand, eventData)) return false;

        Inventory.Read(slot, InventoryId);
        bool loaded = Inventory.Items.Count > 0;
        Inventory.Clear();
        if (!loaded) return false;

        RangedWeaponSystem.SendStatusChange(player, RangedWeaponStatus.TriggeredShot, mainHand);
        SetState(MuzzleloaderState.Shoot, mainHand);
        string animation = GetShootingAnimation(slot, mainHand ? Stats.ShootAnimation : Stats.ShootAnimationOffhand);
        int cycleMs = ++Ak47CycleCounter % 7 == 0 ? 84 : 86; // seven cycles total 600 ms = 700 RPM
        SetNextShotAllowed(mainHand, Api.World.ElapsedMilliseconds + cycleMs);
        AnimationBehavior?.Stop(ItemAnimationCategory(mainHand));
        AnimationBehavior?.Play(mainHand, animation, category: AnimationCategory(mainHand));
        TpAnimationBehavior?.Stop(ItemAnimationCategory(mainHand));
        TpAnimationBehavior?.Play(mainHand, animation, category: AnimationCategory(mainHand));
        Api.World.RegisterCallback(_ => ShootAnimationCallback("shoot", slot, player, mainHand), 0);
        Api.World.RegisterCallback(_ => ShootCallback(slot, player, mainHand), cycleMs);
        return true;
    }

    [ActionEventHandler(EnumEntityAction.RightMouseDown, ActionState.Active)]
    protected override bool Load(ItemSlot slot, EntityPlayer player, ref int state, ActionEventData eventData, bool mainHand, AttackDirection direction)
    {
        if (!EmptyReloadSession && LeftInMagazine(slot) > 0) return false;
        bool started = base.Load(slot, player, ref state, eventData, mainHand, direction);
        if (started) EmptyReloadSession = true;
        return started;
    }

    public override void OnSelected(ItemSlot slot, EntityPlayer player, bool mainHand, ref int state)
    {
        EmptyReloadSession = false;
        base.OnSelected(slot, player, mainHand, ref state);
    }

    public override void OnDeselected(EntityPlayer player, bool mainHand, ref int state)
    {
        EmptyReloadSession = false;
        base.OnDeselected(player, mainHand, ref state);
    }

    protected override void LoadServerCallback(bool success, bool lastAmmoToLoad, bool mainHand, int reloadActionId, ItemSlot slot, int expectedMagazineCount)
    {
        base.LoadServerCallback(success, lastAmmoToLoad, mainHand, reloadActionId, slot, expectedMagazineCount);
        if (reloadActionId == ReloadActionId && (!success || lastAmmoToLoad)) EmptyReloadSession = false;
    }

    protected override void LoadAnimationCallback(string callback, ItemSlot bulletSlot, EntityPlayer player, bool mainHand, int reloadActionId)
    {
        // The reload can consume the last item before this delayed animation callback runs.
        if (callback == "attach" && bulletSlot.Itemstack == null) return;
        base.LoadAnimationCallback(callback, bulletSlot, player, mainHand, reloadActionId);
    }

    [ActionEventHandler(EnumEntityAction.RightMouseDown, ActionState.Released)]
    protected override bool Ease(ItemSlot slot, EntityPlayer player, ref int state, ActionEventData eventData, bool mainHand, AttackDirection direction)
    {
        EmptyReloadSession = false;
        MuzzleloaderState current = (MuzzleloaderState)state;

        bool partiallyLoaded = (current == MuzzleloaderState.Loading || current == MuzzleloaderState.Unloaded) && LeftInMagazine(slot) > 0;
        if (!partiallyLoaded)
        {
            return base.Ease(slot, player, ref state, eventData, mainHand, direction);
        }

        PlayerBehavior?.SetStat("walkspeed", mainHand ? PlayerStatsMainHandCategory : PlayerStatsOffHandCategory);

        if (current == MuzzleloaderState.Loading)
        {
            ReloadActionId++; // cancels the round that was in flight
            Attachable.ClearAttachments(player.EntityId);
            RangedWeaponSystem.SendStatusChange(player, RangedWeaponStatus.EndLoading, mainHand);
        }

        SetState(MuzzleloaderState.Loaded, mainHand);

        AnimationBehavior?.Play(mainHand, GetLoadingAnimation(slot, Stats.LoadedAnimation), category: ItemAnimationCategory(mainHand), weight: 0.001f);
        TpAnimationBehavior?.Play(mainHand, GetLoadingAnimation(slot, Stats.LoadedAnimation), category: ItemAnimationCategory(mainHand), weight: 0.001f);
        AnimationBehavior?.PlayReadyAnimation(mainHand);
        TpAnimationBehavior?.PlayReadyAnimation(mainHand);

        return false;
    }
}

public class RepeaterServer : MuzzleloaderServer
{
    public RepeaterServer(ICoreServerAPI api, Item item) : base(api, item)
    {
    }
}

public sealed class Ak47Client : RepeaterClient
{
    public Ak47Client(ICoreClientAPI api, Item item) : base(api, item) { }
}

public sealed class Ak47Server : RepeaterServer
{
    public Ak47Server(ICoreServerAPI api, Item item) : base(api, item) { }

    public override bool Reload(IServerPlayer player, ItemSlot slot, ItemSlot? ammoSlot, ReloadPacket packet)
    {
        bool loadingMagazine = ammoSlot?.Itemstack?.Item?.Code.Path == "ak47mag" && packet.Amount > 0;
        bool ejectEmpty = loadingMagazine && slot.Itemstack?.Attributes.GetBool("ak47mag-loaded") == true;
        Inventory.Read(slot, InventoryId);
        bool empty = Inventory.Items.Count == 0;
        Inventory.Clear();

        if (!base.Reload(player, slot, ammoSlot, packet)) return false;
        if (loadingMagazine) slot.Itemstack?.Attributes.SetBool("ak47mag-loaded", true);
        if (ejectEmpty && empty)
        {
            Item? emptyMag = Api.World.GetItem(new AssetLocation("smokelesslever:ak47mag-empty"));
            if (emptyMag != null)
            {
                ItemStack stack = new(emptyMag);
                if (!player.InventoryManager.TryGiveItemstack(stack, true))
                    Api.World.SpawnItemEntity(stack, player.Entity.Pos.XYZ);
            }
        }
        slot.MarkDirty();
        return true;
    }
}

public class RepeaterItem : Item, IHasWeaponLogic, IHasRangedWeaponLogic, IHasDynamicIdleAnimations
{
    public RepeaterClient? ClientLogic { get; private set; }
    public RepeaterServer? ServerLogic { get; private set; }

    public AnimationRequestByCode IdleAnimation { get; private set; }
    public AnimationRequestByCode ReadyAnimation { get; private set; }
    public AnimationRequestByCode IdleAnimationOffhand { get; private set; }
    public AnimationRequestByCode ReadyAnimationOffhand { get; private set; }

    public MuzzleloaderStats? Stats { get; private set; }

    protected virtual RepeaterClient CreateClientLogic(ICoreClientAPI api) => new(api, this);
    protected virtual RepeaterServer CreateServerLogic(ICoreServerAPI api) => new(api, this);

    IClientWeaponLogic? IHasWeaponLogic.ClientLogic
    {
        get
        {
            if (ClientLogic == null && _clientApi != null)
            {
                TryInitClientLogic(_clientApi);
            }
            return ClientLogic;
        }
    }

    IServerRangedWeaponLogic? IHasRangedWeaponLogic.ServerWeaponLogic
    {
        get
        {
            if (ServerLogic == null && _serverApi != null)
            {
                TryInitServerLogic(_serverApi);
            }
            return ServerLogic;
        }
    }

    public AnimationRequestByCode? GetIdleAnimation(EntityPlayer player, ItemSlot slot, bool mainHand) => mainHand ? IdleAnimation : IdleAnimationOffhand;
    public AnimationRequestByCode? GetReadyAnimation(EntityPlayer player, ItemSlot slot, bool mainHand) => mainHand ? ReadyAnimation : ReadyAnimationOffhand;

    public override void GetHeldItemInfo(ItemSlot inSlot, StringBuilder dsc, IWorldAccessor world, bool withDebugInfo)
    {
        if (Stats != null && Stats.ProficiencyStat != "")
        {
            dsc.AppendLine(Lang.Get("combatoverhaul:iteminfo-proficiency", Lang.Get($"combatoverhaul:proficiency-{Stats.ProficiencyStat}")));
        }

        if (Stats != null)
        {
            dsc.AppendLine(Lang.Get("combatoverhaul:iteminfo-range-weapon-damage", Stats.BulletDamageMultiplier, Stats.BulletDamageStrength));

            ItemInventoryBuffer magazine = new();
            magazine.Read(inSlot, "magazine");
            dsc.AppendLine(Lang.Get("smokelesslever:iteminfo-rounds", magazine.Items.Count, Stats.MagazineSize));
            magazine.Clear();

            dsc.AppendLine("");
        }

        base.GetHeldItemInfo(inSlot, dsc, world, withDebugInfo);
    }

    public override int GetRemainingDurability(ItemStack itemstack)
    {
        int durability = base.GetRemainingDurability(itemstack);
        int maxDurability = GetMaxDurability(itemstack);
        if (durability > maxDurability)
        {
            itemstack.Attributes.RemoveAttribute("durability");
            return maxDurability;
        }
        return durability;
    }

    public override void OnLoaded(ICoreAPI api)
    {
        base.OnLoaded(api);

        if (api is ICoreClientAPI clientAPI)
        {
            MuzzleloaderStats stats = Attributes.AsObject<MuzzleloaderStats>()
                ?? throw new InvalidOperationException($"Missing muzzleloader stats for {Code}");
            Stats = stats;
            IdleAnimation = new(stats.IdleAnimation, 1, 1, "main", TimeSpan.FromSeconds(0.2), TimeSpan.FromSeconds(0.2), false);
            ReadyAnimation = new(stats.ReadyAnimation, 1, 1, "main", TimeSpan.FromSeconds(0.2), TimeSpan.FromSeconds(0.2), false);
            IdleAnimationOffhand = new(stats.IdleAnimationOffhand, 1, 1, "mainOffhand", TimeSpan.FromSeconds(0.2), TimeSpan.FromSeconds(0.2), false);
            ReadyAnimationOffhand = new(stats.ReadyAnimationOffhand, 1, 1, "mainOffhand", TimeSpan.FromSeconds(0.2), TimeSpan.FromSeconds(0.2), false);
            _clientApi = clientAPI;
        }

        if (api is ICoreServerAPI serverAPI)
        {
            _serverApi = serverAPI;
            Stats = Attributes.AsObject<MuzzleloaderStats>();
            TryInitServerLogic(serverAPI);
        }
    }

    public override void OnCreatedByCrafting(ItemSlot[] allInputslots, ItemSlot outputSlot, IRecipeBase byRecipe)
    {
        base.OnCreatedByCrafting(allInputslots, outputSlot, byRecipe);

        GeneralUtils.MarkItemStack(outputSlot);
        outputSlot.MarkDirty();
    }

    private ICoreClientAPI? _clientApi;
    private ICoreServerAPI? _serverApi;

    private void TryInitClientLogic(ICoreClientAPI clientAPI)
    {
        try
        {
            ClientLogic = CreateClientLogic(clientAPI);
        }
        catch (Exception exception)
        {
            clientAPI.Logger.Warning($"[smokelesslever] Delayed client logic init for {Code}: {exception.Message}");
        }
    }

    private void TryInitServerLogic(ICoreServerAPI serverAPI)
    {
        try
        {
            ServerLogic = CreateServerLogic(serverAPI);
        }
        catch (Exception exception)
        {
            serverAPI.Logger.Warning($"[smokelesslever] Delayed server logic init for {Code}: {exception.Message}");
        }
    }
}

public sealed class Ak47Item : RepeaterItem
{
    protected override RepeaterClient CreateClientLogic(ICoreClientAPI api) => new Ak47Client(api, this);
    protected override RepeaterServer CreateServerLogic(ICoreServerAPI api) => new Ak47Server(api, this);
}
