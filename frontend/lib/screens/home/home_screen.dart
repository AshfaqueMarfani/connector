import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:go_router/go_router.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';

import '../../config/theme.dart';
import '../../models/location.dart';
import '../../providers/location_provider.dart';
import '../../providers/profile_provider.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final MapController _mapController = MapController();
  String? _filterType;

  // Default center: Karachi (seed data area)
  static const _defaultCenter = LatLng(24.8607, 67.0011);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initializeData();
    });
  }

  Future<void> _initializeData() async {
    final locationProvider = context.read<LocationProvider>();
    final profileProvider = context.read<ProfileProvider>();

    // Fetch profile and location in parallel
    await Future.wait([
      profileProvider.fetchMyProfile(),
      locationProvider.fetchMyLocation(),
    ]);

    // Try to update device location
    await locationProvider.updateLocation();

    // Search nearby
    await locationProvider.searchNearby();
  }

  void _onFilterChanged(String? type) {
    setState(() => _filterType = type);
    context.read<LocationProvider>().searchNearby(type: type);
  }

  LatLng get _currentCenter {
    final loc = context.read<LocationProvider>().myLocation;
    if (loc != null) return LatLng(loc.latitude, loc.longitude);
    return _defaultCenter;
  }

  @override
  Widget build(BuildContext context) {
    final locationProvider = context.watch<LocationProvider>();
    final nearbyUsers = locationProvider.nearbyUsers;
    final myLocation = locationProvider.myLocation;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Explore Nearby'),
        actions: [
          // Radius selector
          PopupMenuButton<int>(
            icon: const Icon(Icons.tune),
            tooltip: 'Search radius',
            onSelected: (radius) {
              locationProvider.searchRadius = radius;
              locationProvider.searchNearby(
                  radius: radius, type: _filterType);
            },
            itemBuilder: (_) => [
              for (final r in [100, 250, 500, 1000, 2000, 5000])
                PopupMenuItem(
                  value: r,
                  child: Text(r >= 1000 ? '${r ~/ 1000}km' : '${r}m'),
                ),
            ],
          ),
          // Create status
          IconButton(
            icon: const Icon(Icons.add_circle_outline),
            tooltip: 'Broadcast need/offer',
            onPressed: () => context.push('/status/create'),
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter chips
          _buildFilterBar(),

          // Map
          Expanded(
            child: Stack(
              children: [
                FlutterMap(
                  mapController: _mapController,
                  options: MapOptions(
                    initialCenter: _currentCenter,
                    initialZoom: 14,
                    minZoom: 10,
                    maxZoom: 18,
                  ),
                  children: [
                    TileLayer(
                      urlTemplate:
                          'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                      userAgentPackageName: 'dev.connector.app',
                    ),
                    // Radius circle
                    if (myLocation != null)
                      CircleLayer(circles: [
                        CircleMarker(
                          point: LatLng(
                              myLocation.latitude, myLocation.longitude),
                          radius: locationProvider.searchRadius.toDouble(),
                          useRadiusInMeter: true,
                          color: AppTheme.primaryColor.withOpacity(0.08),
                          borderColor:
                              AppTheme.primaryColor.withOpacity(0.3),
                          borderStrokeWidth: 2,
                        ),
                      ]),
                    // My location marker
                    if (myLocation != null)
                      MarkerLayer(markers: [
                        Marker(
                          point: LatLng(
                              myLocation.latitude, myLocation.longitude),
                          width: 40,
                          height: 40,
                          child: Container(
                            decoration: BoxDecoration(
                              color: AppTheme.primaryColor,
                              shape: BoxShape.circle,
                              border: Border.all(
                                  color: Colors.white, width: 3),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withOpacity(0.2),
                                  blurRadius: 6,
                                ),
                              ],
                            ),
                            child: const Icon(Icons.person,
                                color: Colors.white, size: 18),
                          ),
                        ),
                      ]),
                    // Nearby user markers
                    MarkerLayer(
                      markers: nearbyUsers.map((user) {
                        final color =
                            AppTheme.accountTypeColor(user.accountType);
                        return Marker(
                          point: LatLng(user.latitude, user.longitude),
                          width: 36,
                          height: 36,
                          child: GestureDetector(
                            onTap: () => _showUserSheet(context, user),
                            child: Container(
                              decoration: BoxDecoration(
                                color: color,
                                shape: BoxShape.circle,
                                border: Border.all(
                                    color: Colors.white, width: 2),
                                boxShadow: [
                                  BoxShadow(
                                    color: color.withOpacity(0.4),
                                    blurRadius: 4,
                                  ),
                                ],
                              ),
                              child: Icon(
                                _accountTypeIcon(user.accountType),
                                color: Colors.white,
                                size: 16,
                              ),
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ],
                ),
                // Loading indicator
                if (locationProvider.isLoading)
                  const Positioned(
                    top: 8,
                    left: 0,
                    right: 0,
                    child: Center(
                      child: CircularProgressIndicator(),
                    ),
                  ),
                // Result count badge
                Positioned(
                  bottom: 16,
                  left: 16,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: Theme.of(context)
                          .colorScheme
                          .surface
                          .withOpacity(0.9),
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.1),
                          blurRadius: 8,
                        ),
                      ],
                    ),
                    child: Text(
                      '${locationProvider.totalNearby} people nearby '
                      '(${locationProvider.searchRadius}m)',
                      style: const TextStyle(
                          fontWeight: FontWeight.w500, fontSize: 13),
                    ),
                  ),
                ),
                // Recenter button
                Positioned(
                  bottom: 16,
                  right: 16,
                  child: FloatingActionButton.small(
                    heroTag: 'recenter',
                    onPressed: () {
                      if (myLocation != null) {
                        _mapController.move(
                          LatLng(myLocation.latitude, myLocation.longitude),
                          14,
                        );
                      }
                    },
                    child: const Icon(Icons.my_location),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        heroTag: 'refresh_location',
        onPressed: () async {
          await locationProvider.updateLocation();
          await locationProvider.searchNearby(type: _filterType);
        },
        child: const Icon(Icons.refresh),
      ),
    );
  }

  Widget _buildFilterBar() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          _filterChip('All', null),
          const SizedBox(width: 8),
          _filterChip('Individuals', 'individual'),
          const SizedBox(width: 8),
          _filterChip('Businesses', 'business'),
          const SizedBox(width: 8),
          _filterChip('NGOs', 'ngo'),
        ],
      ),
    );
  }

  Widget _filterChip(String label, String? type) {
    final isSelected = _filterType == type;
    return FilterChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (_) => _onFilterChanged(type),
      selectedColor: AppTheme.primaryColor.withOpacity(0.15),
      checkmarkColor: AppTheme.primaryColor,
    );
  }

  IconData _accountTypeIcon(String type) {
    switch (type) {
      case 'business':
        return Icons.store;
      case 'ngo':
        return Icons.volunteer_activism;
      default:
        return Icons.person;
    }
  }

  void _showUserSheet(BuildContext context, NearbyUser user) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor:
                      AppTheme.accountTypeColor(user.accountType),
                  radius: 24,
                  child: Icon(
                    _accountTypeIcon(user.accountType),
                    color: Colors.white,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        user.displayName,
                        style: const TextStyle(
                            fontWeight: FontWeight.w600, fontSize: 16),
                      ),
                      Text(
                        '${user.accountType.toUpperCase()} • '
                        '${user.distanceMeters.round()}m away${user.isExact ? '' : ' (approx)'}',
                        style: TextStyle(
                            color: Colors.grey[600], fontSize: 13),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // Skills/tags from profile data
            if ((user.profileData['skills'] as List?)?.isNotEmpty ?? false)
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: (user.profileData['skills'] as List)
                    .take(6)
                    .map((s) => Chip(
                          label: Text(s.toString(), style: const TextStyle(fontSize: 12)),
                          materialTapTargetSize:
                              MaterialTapTargetSize.shrinkWrap,
                          visualDensity: VisualDensity.compact,
                        ))
                    .toList(),
              ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.person),
                    label: const Text('View Profile'),
                    onPressed: () {
                      Navigator.pop(context);
                      context.push('/profile/${user.userId}');
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.connect_without_contact),
                    label: const Text('Connect'),
                    onPressed: () {
                      Navigator.pop(context);
                      context.push('/profile/${user.userId}');
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }
}
